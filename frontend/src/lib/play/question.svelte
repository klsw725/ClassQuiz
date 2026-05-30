<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import type { Answer, OrderQuizAnswer, Question, RangeQuizAnswer, TextQuizAnswer } from '$lib/quiz_types';
	import { QuizQuestionType } from '$lib/quiz_types';
	import { socket } from '$lib/socket';
	import Spinner from '../Spinner.svelte';
	import { getLocalization } from '$lib/i18n';
	import { kahoot_icons } from './kahoot_mode_assets/kahoot_icons';
	import CircularTimer from '$lib/play/circular_progress.svelte';
	import { flip } from 'svelte/animate';
	import BrownButton from '$lib/components/buttons/brown.svelte';
	import { get_foreground_color } from '../helpers';
	import MediaComponent from '$lib/editor/MediaComponent.svelte';

	const { t } = getLocalization();

	interface Props {
		question: Question;
		game_mode: any;
		question_index: string | number;
		solution: Question | undefined;
	}

	let {
		question = $bindable(),
		game_mode = $bindable(),
		question_index,
		solution
	}: Props = $props();

	if (question.type === undefined) {
		question.type = QuizQuestionType.ABCD;
	} else {
		question.type = QuizQuestionType[question.type];
	}

	let timer_res = $state(question.time);
	let selected_answer: string = $state();
	let answer_submitted = $state(false);

	// Stop the timer if the question is answered
	const timer = (time: string) => {
		let seconds = Number(time);
		let timer_interval = setInterval(() => {
			if (timer_res === '0') {
				clearInterval(timer_interval);
				return;
			} else {
				seconds--;
			}

			timer_res = seconds.toString();
		}, 1000);
	};
	socket.on('everyone_answered', (_) => {
		timer_res = '0';
	});

	timer(question.time);

	$effect(() => {
		if (solution !== undefined) {
			timer_res = '0';
		}
	});

	const selectAnswer = (answer: string) => {
		selected_answer = answer;
		answer_submitted = true;
		socket.emit('submit_answer', {
			question_index: question_index,
			answer: answer
		});
	};

	const select_complex_answer = (data) => {
		selected_answer = 'a';
		answer_submitted = true;
		const new_array = [];
		for (let i = 0; i < data.length; i++) {
			new_array.push({ answer: data[i].answer });
		}
		socket.emit('submit_answer', {
			question_index: question_index,
			answer: 'a',
			complex_answer: new_array
		});
	};

	let text_input = $state('');

	let slider_value = $state([0]);
	if (question.type === QuizQuestionType.RANGE) {
		const range_answer = question.answers as RangeQuizAnswer;
		slider_value[0] = (range_answer.max - range_answer.min) / 2 + range_answer.min;
	}
	const set_answer_if_not_set_range = (time) => {
		if (question.type !== QuizQuestionType.RANGE) {
			return;
		}
		if (selected_answer === undefined && time === '0') {
			selected_answer = `${slider_value[0]}`;
			selectAnswer(selected_answer);
		}
	};

	if (question.type === QuizQuestionType.ORDER) {
		for (let i = 0; i < question.answers.length; i++) {
			question.answers[i] = { ...question.answers[i], id: i };
		}
	}

	const swapArrayElements = (arr, a: number, b: number) => {
		let _arr = [...arr];
		let temp = _arr[a];
		_arr[a] = _arr[b];
		_arr[b] = temp;
		return _arr;
	};
	$effect(() => {
		set_answer_if_not_set_range(timer_res);
	});
	let circular_progress = $derived.by(() => {
		try {
			return 1 - ((100 / parseInt(question.time)) * parseInt(timer_res)) / 100;
		} catch {
			return 0;
		}
	});

	const get_div_height = (): string => {
		if (game_mode === 'normal' || (game_mode === 'kahoot' && question.image)) {
			if (question.image) {
				return '66.666667';
			} else {
				return '83.333333';
			}
		} else {
			return '100';
		}
	};

	const get_question_area_height = (): string => {
		if (solution !== undefined) {
			return '50';
		}
		return question.image ? '33.333333' : '16.666667';
	};

	const revealed_answers = $derived.by((): string[] => {
		if (solution === undefined) {
			return [];
		}

		const solution_type = solution.type ?? QuizQuestionType.ABCD;

		if (solution_type === QuizQuestionType.RANGE) {
			const answer = solution.answers as RangeQuizAnswer;
			return [`${answer.min_correct} - ${answer.max_correct}`];
		}

		if (solution_type === QuizQuestionType.TEXT) {
			return (solution.answers as TextQuizAnswer[]).map((answer) => answer.answer);
		}

		if (solution_type === QuizQuestionType.ORDER) {
			return (solution.answers as OrderQuizAnswer[]).map((answer) => answer.answer);
		}

		if (solution_type === QuizQuestionType.ABCD || solution_type === QuizQuestionType.CHECK) {
			return (solution.answers as Answer[])
				.filter((answer) => answer.right)
				.map((answer) => answer.answer);
		}

		return [];
	});

	const is_voting_reveal = $derived(
		solution !== undefined && (solution.type ?? QuizQuestionType.ABCD) === QuizQuestionType.VOTING
	);

	const default_colors = ['#D6EDC9', '#B07156', '#7F7057', '#4E6E58'];
</script>

<div class="h-screen w-screen">
	{#if solution !== undefined || game_mode === 'normal' || (game_mode === 'kahoot' && question.image)}
		<div
			class="flex flex-col justify-start"
			class:mt-10={solution === undefined &&
				[QuizQuestionType.RANGE, QuizQuestionType.ORDER, QuizQuestionType.TEXT].includes(
					question.type
				)}
			style="height: {get_question_area_height()}%"
		>
			<h1
				class="lg:text-2xl text-lg text-center text-cq-text mt-2 break-normal mb-2 notranslate"
				translate="no"
			>
				{@html question.question}
			</h1>
			{#if solution !== undefined}
				<section class="mx-auto flex w-full max-w-3xl flex-col gap-3 px-4 text-center">
					<p class="text-sm font-semibold tracking-wide text-cq-muted uppercase">
						{#if is_voting_reveal}
							{$t('words.voting')} {$t('words.result')}
						{:else}
							{$t('words.correct')} {$t('words.answer')}
						{/if}
					</p>
					{#if is_voting_reveal}
						<div class="cq-card cq-surface-muted border-2 border-cq-border p-5 text-cq-text">
							<p class="text-2xl font-semibold">{$t('words.voting')}</p>
						</div>
					{:else}
						<ul class="flex flex-col gap-2" aria-label="{$t('words.correct')} {$t('words.answer')}">
							{#each revealed_answers as answer, i (i)}
								<li
									class="cq-card cq-surface-muted border-2 border-cq-border px-4 py-3 text-xl font-semibold text-cq-text notranslate"
									translate="no"
								>
									{answer}
								</li>
							{/each}
						</ul>
					{/if}
				</section>
			{:else if question.image}
				<div class="max-h-full">
					<MediaComponent
						src={question.image}
						css_classes="object-cover mx-auto mb-8 max-h-[90%]"
					/>
				</div>
			{/if}
		</div>
	{/if}
	{#if solution === undefined && (answer_submitted || timer_res === '0')}
		<section
			class="flex h-1/2 items-center justify-center px-4 text-cq-text"
			role="status"
			aria-live="polite"
		>
			<div class="cq-card flex w-full max-w-md flex-col gap-3 p-6 text-center shadow-2xl md:p-8">
				<p class="text-2xl font-semibold text-cq-text md:text-3xl">
					{#if answer_submitted}
						{$t('play_page.answer_submitted')}
					{:else}
						{$t('play_page.please_wait')}
					{/if}
				</p>
				<p class="cq-surface-muted rounded-lg border-2 border-cq-border px-5 py-4 text-cq-muted">
					{$t('play_page.waiting_for_results')}
				</p>
			</div>
		</section>
	{:else if timer_res !== '0'}
		{#if question.type === QuizQuestionType.ABCD || question.type === QuizQuestionType.VOTING}
			<div class="w-full relative h-full" style="height: {get_div_height()}%">
				<div
					class="cq-surface absolute top-0 bottom-0 left-0 right-0 m-auto h-fit w-fit rounded-full border-2 border-cq-border shadow-2xl z-40"
				>
					<CircularTimer text={timer_res} progress={circular_progress} color="#ef4444" />
				</div>

				<div class="grid grid-rows-2 grid-flow-col auto-cols-auto gap-2 w-full p-4 h-full">
					{#each question.answers as answer, i}
						<button
							class="rounded-lg h-full flex align-middle justify-center disabled:opacity-60 p-3 border-2 border-cq-border"
							style="background-color: {answer.color ??
								default_colors[i]}; color: {get_foreground_color(
								answer.color ?? default_colors[i]
							)}"
							disabled={selected_answer !== undefined}
							onclick={() => selectAnswer(answer.answer)}
						>
							{#if game_mode === 'kahoot'}
								{#if answer.emoji}
									<span
										class="m-auto text-6xl leading-none"
										aria-label={$t('admin_page.answer_emoji')}>{answer.emoji}</span
									>
								{:else}
									<img
										class="h-2/3 inline-block m-auto"
										alt={$t('admin_page.answer_icon')}
										src={kahoot_icons[i]}
									/>
								{/if}
							{:else if game_mode === 'normal'}
								<div class="m-auto flex items-center justify-center gap-3">
									{#if answer.emoji}
										<span class="text-4xl leading-none" aria-label={$t('admin_page.answer_emoji')}
											>{answer.emoji}</span
										>
									{:else if kahoot_icons[i]}
										<img class="h-12" alt={$t('admin_page.answer_icon')} src={kahoot_icons[i]} />
									{/if}
									<p class="notranslate" translate="no">{answer.answer}</p>
								</div>
							{:else}
								<p class="m-auto notranslate" translate="no">{answer.answer}</p>
							{/if}
						</button>
					{/each}
				</div>
			</div>
		{:else if question.type === QuizQuestionType.RANGE}
			{@const range_answer = question.answers as RangeQuizAnswer}
			<span
				class="fixed top-0 bg-red-500 h-8 transition-all"
				style="width: {(100 / parseInt(question.time)) * parseInt(timer_res)}vw"
			></span>
			{#await import('svelte-range-slider-pips')}
				<Spinner />
			{:then c}
				<div class:pointer-events-none={selected_answer !== undefined} class="mt-24">
					<c.default
						bind:values={slider_value}
						bind:min={range_answer.min}
						bind:max={range_answer.max}
						id="pips-slider"
						pips
						float
						all="label"
					/>
				</div>
				<div class="flex justify-center">
					<div class="w-1/2">
						<BrownButton onclick={() => selectAnswer(String(slider_value[0]))}
							>{$t('words.submit')}
						</BrownButton>
					</div>
				</div>
			{/await}
		{:else if question.type === QuizQuestionType.TEXT}
			<div>
				<span
					class="fixed top-0 bg-red-500 h-8 transition-all"
					style="width: {(100 / parseInt(question.time)) * parseInt(timer_res)}vw"
				></span>
				<div class="flex justify-center mt-10">
					<p class="text-cq-text">{$t('editor.enter_answer')}</p>
				</div>
				<div class="flex justify-center m-2">
					<input
						type="text"
						bind:value={text_input}
						disabled={selected_answer !== undefined}
						class="cq-surface-muted block w-full p-2 text-center text-cq-text outline-hidden ring-2 ring-cq-border transition focus:ring-cq-brand disabled:cursor-not-allowed disabled:opacity-50"
					/>
				</div>

				<div class="flex justify-center mt-2">
					<div class="w-1/3">
						<BrownButton
							type="button"
							disabled={!text_input || text_input.length === 0}
							onclick={() => {
								selectAnswer(text_input);
							}}
						>
							{$t('words.submit')}
						</BrownButton>
					</div>
				</div>
			</div>
		{:else if question.type === QuizQuestionType.ORDER}
			<!--			{#if solution === undefined}
                            <Spinner />
                        {:else}-->
			<span
				class="fixed top-0 bg-red-500 h-8 transition-all"
				style="width: {(100 / parseInt(question.time)) * parseInt(timer_res)}vw"
			></span>
			<div class="flex flex-col w-full h-full gap-4 px-4 py-6 mt-10">
				{#each question.answers as answer, i (answer.id)}
					<div
						class="cq-card w-full h-fit flex-row p-2 align-middle"
						animate:flip={{ duration: 100 }}
						style="background-color: {answer.color ?? '#b07156'}"
					>
						<button
							onclick={() => {
								question.answers = swapArrayElements(question.answers, i, i - 1);
							}}
							class="action-button w-full flex justify-center p-2 disabled:opacity-50"
							type="button"
							aria-label={$t('solo_page.move_up')}
							disabled={i === 0 || Boolean(selected_answer)}
						>
							<svg
								class="w-8 h-8"
								stroke-width="2"
								viewBox="0 0 24 24"
								fill="none"
								xmlns="http://www.w3.org/2000/svg"
								color="currentColor"
							>
								<path
									d="M12 22a2 2 0 110-4 2 2 0 010 4zM12 15V2m0 0l3 3m-3-3L9 5"
									stroke="currentColor"
									stroke-width="2"
									stroke-linecap="round"
									stroke-linejoin="round"
								/>
							</svg>
						</button>
						<p class="w-full text-center p-2 text-2xl text-cq-text notranslate" translate="no">
							{answer.answer}
						</p>

						<button
							onclick={() => {
								question.answers = swapArrayElements(question.answers, i, i + 1);
							}}
							class="action-button w-full flex justify-center p-2 disabled:opacity-50"
							type="button"
							aria-label={$t('solo_page.move_down')}
							disabled={i === question.answers.length - 1 || Boolean(selected_answer)}
						>
							<svg
								class="w-8 h-8"
								stroke-width="2"
								viewBox="0 0 24 24"
								fill="none"
								xmlns="http://www.w3.org/2000/svg"
								color="currentColor"
							>
								<path
									d="M12 6a2 2 0 110-4 2 2 0 010 4zM12 9v13m0 0l3-3m-3 3l-3-3"
									stroke="currentColor"
									stroke-width="2"
									stroke-linecap="round"
									stroke-linejoin="round"
								/>
							</svg>
						</button>
					</div>
				{/each}
				<div class="w-full mt-2">
					<BrownButton
						type="button"
						disabled={Boolean(selected_answer)}
						onclick={() => {
							select_complex_answer(question.answers as OrderQuizAnswer[]);
						}}>{$t('words.submit')}</BrownButton
					>
				</div>
			</div>
			<!--{/if}-->
		{:else if question.type === QuizQuestionType.CHECK}
			{#await import('./questions/check.svelte')}
				<Spinner />
			{:then c}
				<c.default
					{question}
					bind:selected_answer
					{game_mode}
					{timer_res}
					{circular_progress}
				/>
				<div class="flex justify-center h-[5%]">
					<div class="w-1/2">
						<BrownButton
							type="button"
							disabled={selected_answer === undefined}
							onclick={() => selectAnswer(selected_answer)}
							>{$t('words.submit')}
						</BrownButton>
					</div>
				</div>
			{/await}
		{/if}
	{:else if solution !== undefined}
		<section class="flex h-1/2 items-center justify-center px-4 text-cq-text" aria-live="polite">
			<div class="cq-card flex w-full max-w-md flex-col gap-4 p-6 text-center shadow-2xl md:p-8">
				<p
					class="cq-surface-muted rounded-lg border-2 border-cq-border px-5 py-4 text-2xl font-semibold text-cq-brand md:text-3xl"
				>
					{$t('words.score')} {$t('words.public')}
				</p>
				<p class="text-cq-muted">{$t('words.result')} {$t('words.public')}</p>
			</div>
		</section>
	{/if}
</div>
