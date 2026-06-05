<!--
SPDX-FileCopyrightText: 2026 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import { browser } from '$app/environment';
	import BrownButton from '$lib/components/buttons/brown.svelte';
	import GrayButton from '$lib/components/buttons/gray.svelte';
	import MediaComponent from '$lib/editor/MediaComponent.svelte';
	import Spinner from '$lib/Spinner.svelte';
	import type {
		Answer,
		OrderQuizAnswer,
		Question,
		RangeQuizAnswer,
		TextQuizAnswer
	} from '$lib/quiz_types';
	import { QuizQuestionType } from '$lib/quiz_types';
	import { getLocalization } from '$lib/i18n';
	import { flip } from 'svelte/animate';
	import { onDestroy } from 'svelte';

	interface Props {
		data: { pin: string; token: string };
	}

	interface SoloAttemptState {
		attempt_id: string;
		game_pin: string;
		username: string;
		zone: string;
		title: string;
		description: string;
		current_question: number;
		question_count: number;
		total_score: number;
		completed: boolean;
		question: Question | null;
	}

	interface SoloSubmitResult {
		right: boolean;
		score: number;
		total_score: number;
		completed: boolean;
		solution?: Question | null;
	}

	interface SubmitPayload {
		question_index: number;
		answer?: string | number;
		complex_answer?: { answer: string }[];
	}

	const { t } = getLocalization();

	let { data }: Props = $props();
	let game_pin = $state(data.pin);
	let token = $state(data.token);
	let username = $state('');
	let zone = $state('1구역');
	let attempt = $state<SoloAttemptState>();
	let current_question = $state<Question | null>(null);
	let current_question_index = $state(0);
	let submit_result = $state<SoloSubmitResult>();
	let loading = $state(false);
	let error_message = $state('');
	let timer_res = $state('0');
	let timer_interval: ReturnType<typeof setInterval> | undefined = undefined;
	let text_inputs = $state<string[]>([]);
	let range_value = $state([0]);
	let selected_check_answers = $state<boolean[]>([]);
	let copy_status = $state('');
	const zones = Array.from({ length: 11 }, (_, index) => `${index + 1}구역`);

	let share_url = $derived.by(() => {
		if (!game_pin || !token) {
			return '';
		}
		const params = new URLSearchParams({ pin: game_pin, token });
		if (!browser) {
			return `/solo?${params.toString()}`;
		}
		return `${window.location.origin}/solo?${params.toString()}`;
	});

	let time_progress = $derived.by(() => {
		if (!current_question) {
			return 0;
		}
		const total_time = Number(current_question.time);
		const remaining_time = Number(timer_res);
		if (!Number.isFinite(total_time) || total_time <= 0) {
			return 0;
		}
		return Math.max(0, Math.min(100, (remaining_time / total_time) * 100));
	});
	let has_text_answer = $derived(text_inputs.some((answer) => answer.trim().length > 0));

	const create_text_inputs = (question: Question | null): string[] => {
		if (
			!question ||
			question.type !== QuizQuestionType.MULTI_TEXT ||
			!Array.isArray(question.answers)
		) {
			return [''];
		}
		return Array.from(
			{ length: Math.max((question.answers as TextQuizAnswer[]).length, 1) },
			() => ''
		);
	};

	const clear_timer = () => {
		if (timer_interval) {
			clearInterval(timer_interval);
			timer_interval = undefined;
		}
	};

	const start_timer = (question: Question) => {
		clear_timer();
		let seconds = Number(question.time);
		if (!Number.isFinite(seconds) || seconds < 0) {
			seconds = 0;
		}
		timer_res = String(seconds);
		if (seconds === 0) {
			return;
		}
		timer_interval = setInterval(() => {
			seconds -= 1;
			timer_res = String(Math.max(0, seconds));
			if (seconds <= 0) {
				clear_timer();
				if (!submit_result) {
					if (
						current_question?.type === QuizQuestionType.TEXT ||
						current_question?.type === QuizQuestionType.MULTI_TEXT
					) {
						submit_text_answer();
					} else {
						submit_answer();
					}
				}
			}
		}, 1000);
	};

	const prepare_question = (question: Question | null, question_index: number) => {
		current_question = question;
		current_question_index = question_index;
		submit_result = undefined;
		text_inputs = create_text_inputs(question);
		selected_check_answers = [];
		if (!question) {
			clear_timer();
			return;
		}
		if (question.type === QuizQuestionType.RANGE) {
			const range_answer = question.answers as RangeQuizAnswer;
			range_value = [(range_answer.max - range_answer.min) / 2 + range_answer.min];
		}
		if (question.type === QuizQuestionType.CHECK) {
			selected_check_answers = (question.answers as Answer[]).map(() => false);
		}
		if (question.type === QuizQuestionType.ORDER) {
			question.answers = (question.answers as OrderQuizAnswer[]).map((answer, index) => ({
				...answer,
				id: index
			}));
		}
		start_timer(question);
	};

	const create_attempt = async (event: Event) => {
		event.preventDefault();
		if (!game_pin || !token || username.length < 1) {
			return;
		}
		loading = true;
		error_message = '';
		const response = await fetch('/api/v1/solo/attempts', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ game_pin, solo_token: token, username, zone })
		});
		loading = false;
		if (!response.ok) {
			error_message =
				response.status === 404
					? $t('solo_page.game_not_found')
					: $t('solo_page.start_attempt_failed');
			return;
		}
		attempt = (await response.json()) as SoloAttemptState;
		prepare_question(attempt.question, attempt.current_question);
	};

	const submit_answer = async (
		answer?: string | number,
		complex_answer?: { answer: string }[]
	) => {
		if (!attempt || !current_question || submit_result || loading) {
			return;
		}
		clear_timer();
		loading = true;
		error_message = '';
		const payload: SubmitPayload = { question_index: current_question_index };
		if (answer !== undefined) {
			payload.answer = answer;
		}
		if (complex_answer !== undefined) {
			payload.complex_answer = complex_answer;
		}
		const response = await fetch(`/api/v1/solo/attempts/${attempt.attempt_id}/submit`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify(payload)
		});
		loading = false;
		if (!response.ok) {
			error_message = $t('solo_page.submit_failed');
			return;
		}
		submit_result = (await response.json()) as SoloSubmitResult;
		attempt = {
			...attempt,
			total_score: submit_result.total_score,
			completed: submit_result.completed,
			current_question: submit_result.completed
				? current_question_index + 1
				: current_question_index
		};
	};

	const submit_check_answer = () => {
		const answer = selected_check_answers
			.map((selected, index) => (selected ? String(index) : ''))
			.join('');
		submit_answer(answer);
	};

	const submit_order_answer = () => {
		if (!current_question || current_question.type !== QuizQuestionType.ORDER) {
			return;
		}
		const complex_answer = (current_question.answers as OrderQuizAnswer[]).map((answer) => ({
			answer: answer.answer
		}));
		submit_answer('a', complex_answer);
	};

	const submit_text_answer = () => {
		if (!current_question) {
			return;
		}
		if (current_question.type === QuizQuestionType.MULTI_TEXT) {
			submit_answer(
				text_inputs.join(', '),
				text_inputs.map((answer) => ({ answer }))
			);
			return;
		}
		submit_answer(text_inputs[0] ?? '');
	};

	const show_next_question = async () => {
		if (!attempt || !submit_result || loading) {
			return;
		}
		loading = true;
		error_message = '';
		const response = await fetch(`/api/v1/solo/attempts/${attempt.attempt_id}/advance`, {
			method: 'POST'
		});
		loading = false;
		if (!response.ok) {
			error_message = $t('solo_page.next_question_failed');
			return;
		}
		attempt = (await response.json()) as SoloAttemptState;
		prepare_question(attempt.question, attempt.current_question);
	};

	const copy_share_url = async (event: MouseEvent) => {
		event.preventDefault();
		if (!share_url || !browser) {
			return;
		}
		try {
			await navigator.clipboard.writeText(share_url);
			copy_status = $t('components.popover.copied_to_clipboard');
		} catch {
			copy_status = $t('components.popover.copy_failed');
		}
	};

	const swap_array_elements = (answers: OrderQuizAnswer[], from: number, to: number) => {
		const next_answers = [...answers];
		const moving_answer = next_answers[from];
		next_answers[from] = next_answers[to];
		next_answers[to] = moving_answer;
		return next_answers;
	};

	const solution_answers = (solution: Question) => {
		if (solution.type === QuizQuestionType.RANGE) {
			const answer = solution.answers as RangeQuizAnswer;
			return [`${answer.min_correct} - ${answer.max_correct}`];
		}
		if (solution.type === QuizQuestionType.TEXT || solution.type === QuizQuestionType.MULTI_TEXT) {
			return (solution.answers as TextQuizAnswer[]).map((answer) => answer.answer);
		}
		if (solution.type === QuizQuestionType.ORDER) {
			return (solution.answers as OrderQuizAnswer[]).map((answer) => answer.answer);
		}
		if (solution.type === QuizQuestionType.ABCD || solution.type === QuizQuestionType.CHECK) {
			return (solution.answers as Answer[])
				.filter((answer) => answer.right)
				.map((answer) => answer.answer);
		}
		return [];
	};

	onDestroy(() => {
		clear_timer();
	});
</script>

<svelte:head>
	<title>ClassQuiz - {$t('solo_page.meta.title')}</title>
</svelte:head>

<div class="min-h-screen px-4 py-8 text-cq-text">
	{#if !attempt}
		<div class="mx-auto flex min-h-[80vh] w-full max-w-2xl items-center justify-center">
			<form
				class="cq-card flex w-full flex-col gap-5 p-6 text-center"
				onsubmit={create_attempt}
			>
				<div>
					<p class="text-sm font-semibold uppercase tracking-wide text-cq-muted">
						{$t('solo_page.preview')}
					</p>
					<h1 class="mt-2 text-3xl font-bold text-cq-text">{$t('solo_page.play_at_your_pace')}</h1>
				</div>

				<label class="flex flex-col gap-2 text-left font-semibold text-cq-text">
					PIN
					<input
						class="cq-surface-muted w-full p-3 text-center text-2xl tracking-widest outline-hidden ring-2 ring-cq-border transition focus:ring-cq-brand"
						bind:value={game_pin}
						maxlength="6"
						inputmode="numeric"
					/>
				</label>

				{#if share_url}
					<div
						class="cq-surface-muted flex flex-col gap-2 p-3 text-left text-sm text-cq-muted"
					>
						<span class="font-semibold text-cq-text">{$t('solo_page.share_link')}</span>
						<span class="break-all">{share_url}</span>
						<button type="button" class="action-button w-full" onclick={copy_share_url}
							>{$t('solo_page.copy_share_link')}</button
						>
						{#if copy_status}<p>{copy_status}</p>{/if}
					</div>
				{/if}

				<label class="flex flex-col gap-2 text-left font-semibold text-cq-text">
					{$t('words.name')}
					<input
						class="cq-surface-muted w-full p-3 text-center outline-hidden ring-2 ring-cq-border transition focus:ring-cq-brand"
						bind:value={username}
						maxlength="17"
					/>
				</label>

				<label class="flex flex-col gap-2 text-left font-semibold text-cq-text">
					{$t('words.zone')}
					<select
						class="cq-surface-muted w-full self-center rounded-lg p-3 text-center text-cq-text outline-hidden ring-2 ring-cq-border transition-all focus:ring-cq-brand"
						bind:value={zone}
					>
						{#each zones as zone_option (zone_option)}
							<option value={zone_option}>{zone_option}</option>
						{/each}
					</select>
				</label>

				{#if error_message}
					<p class="cq-surface-muted p-3 text-cq-text" role="alert">{error_message}</p>
				{/if}

				<BrownButton
					type="submit"
					disabled={loading || !game_pin || !token || username.length < 1}
				>
					{#if loading}<Spinner my_20={false} />{:else}{$t('solo_page.start_attempt')}{/if}
				</BrownButton>
			</form>
		</div>
	{:else if attempt.completed && !submit_result}
		<section class="mx-auto flex min-h-[80vh] w-full max-w-2xl items-center justify-center">
			<div class="cq-card flex w-full flex-col gap-4 p-6 text-center">
				<p class="text-sm font-semibold uppercase tracking-wide text-cq-muted">
					{$t('solo_page.final_score')}
				</p>
				<h1 class="text-4xl font-bold text-cq-text">{attempt.total_score}</h1>
				<p class="text-cq-muted">{$t('solo_page.completed_message', { username: attempt.username })}</p>
				<div class="cq-surface-muted p-3 text-sm text-cq-muted">
					<p class="font-semibold text-cq-text">PIN {attempt.game_pin}</p>
					<p class="break-all">{share_url}</p>
				</div>
			</div>
		</section>
	{:else if current_question}
		{#key current_question_index}
		<div class="mx-auto flex w-full max-w-5xl flex-col gap-4">
			<header
				class="cq-card flex flex-col gap-3 p-4 md:flex-row md:items-center md:justify-between"
			>
				<div>
					<p class="text-sm font-semibold uppercase tracking-wide text-cq-muted">
						{$t('solo_page.question_progress', { current: current_question_index + 1, total: attempt.question_count })}
					</p>
					<h1 class="notranslate text-2xl font-bold text-cq-text" translate="no">
						{@html attempt.title}
					</h1>
					{#if attempt.description}<p class="notranslate text-cq-muted" translate="no">
							{@html attempt.description}
						</p>{/if}
				</div>
				<div class="cq-surface-muted p-3 text-sm text-cq-muted">
					<p class="font-semibold text-cq-text">PIN {attempt.game_pin}</p>
					<p>{$t('play_page.your_score', { score: attempt.total_score })}</p>
				</div>
			</header>

			<section class="cq-card flex flex-col gap-5 p-5">
				<div class="flex flex-col gap-3 text-center">
					<p class="text-sm font-semibold uppercase tracking-wide text-cq-muted">
						{current_question.type ?? QuizQuestionType.ABCD}
					</p>
					<h2 class="notranslate text-3xl font-bold text-cq-text" translate="no">
						{@html current_question.question}
					</h2>
					{#if current_question.image}
						<MediaComponent
							src={current_question.image}
							css_classes="mx-auto max-h-72 w-auto object-contain"
						/>
					{/if}
					{#if !submit_result}
						<div
							class="cq-surface-muted overflow-hidden p-1"
							aria-label={$t('admin_page.time_left')}
						>
							<div
								class="h-3 rounded-sm bg-cq-brand transition-all"
								style="width: {time_progress}%"
							></div>
						</div>
						<p class="text-cq-muted">{timer_res}s</p>
					{/if}
				</div>

				{#if submit_result}
					<div
						class="cq-surface-muted flex flex-col gap-4 p-4 text-center"
						aria-live="polite"
					>
						<p class="text-3xl font-bold text-cq-text">
							{submit_result.right ? $t('words.correct') : $t('words.result')}
						</p>
						<p class="text-xl text-cq-text">{$t('solo_page.points_added', { score: submit_result.score })}</p>
						<p class="text-cq-muted">{$t('solo_page.total_score', { score: submit_result.total_score })}</p>

						{#if submit_result.solution}
							<div class="cq-card flex flex-col gap-2 p-4">
								<p class="font-semibold text-cq-text">{$t('solo_page.solution')}</p>
								{#if submit_result.solution.type === QuizQuestionType.VOTING}
									<p class="text-cq-muted">
										{$t('solo_page.voting_no_correct_answer')}
									</p>
								{:else}
									{#each solution_answers(submit_result.solution) as answer, index (index)}
										<p class="cq-surface-muted notranslate p-2 text-cq-text" translate="no">
											{answer}
										</p>
									{/each}
								{/if}
							</div>
						{/if}

						{#if submit_result.completed}
							<BrownButton
								onclick={() => {
									submit_result = undefined;
									attempt = { ...attempt, completed: true };
								}}
							>
								{$t('solo_page.view_final_score')}
							</BrownButton>
						{:else}
							<BrownButton onclick={show_next_question} disabled={loading}
								>{$t('solo_page.next_question')}</BrownButton
							>
						{/if}
					</div>
				{:else if current_question.type === QuizQuestionType.ABCD || !current_question.type}
					{@const answers = current_question.answers as Answer[]}
					<div class="grid gap-3 md:grid-cols-2">
						{#each answers as answer, index (index)}
							<button
								type="button"
								class="cq-surface-muted cq-card-interactive notranslate p-4 text-center text-cq-text disabled:opacity-60"
								translate="no"
								onclick={() => submit_answer(answer.answer)}
								disabled={loading}
							>
								{answer.answer}
							</button>
						{/each}
					</div>
				{:else if current_question.type === QuizQuestionType.CHECK}
					{@const answers = current_question.answers as Answer[]}
					<div class="flex flex-col gap-3">
						{#each answers as answer, index (index)}
							<button
								type="button"
								class="cq-surface-muted cq-card-interactive notranslate p-4 text-center text-cq-text opacity-60"
								translate="no"
								class:opacity-100={selected_check_answers[index]}
								onclick={() => {
									selected_check_answers[index] = !selected_check_answers[index];
								}}
							>
								{answer.answer}
							</button>
						{/each}
						<BrownButton onclick={submit_check_answer} disabled={loading}
							>{$t('words.submit')}</BrownButton
						>
					</div>
				{:else if current_question.type === QuizQuestionType.RANGE}
					{@const range_answer = current_question.answers as RangeQuizAnswer}
					<div class="flex flex-col gap-5">
						{#await import('svelte-range-slider-pips')}
							<Spinner />
						{:then slider}
							<slider.default
								bind:values={range_value}
								bind:min={range_answer.min}
								bind:max={range_answer.max}
								pips
								float
								all="label"
							/>
						{/await}
						<BrownButton
							onclick={() => submit_answer(range_value[0])}
							disabled={loading}>{$t('words.submit')}</BrownButton
						>
					</div>
				{:else if current_question.type === QuizQuestionType.TEXT || current_question.type === QuizQuestionType.MULTI_TEXT}
					<div class="flex flex-col gap-3">
						{#each text_inputs as _text_input, index (index)}
							<input
								class="cq-surface-muted w-full p-3 text-center outline-hidden ring-2 ring-cq-border transition focus:ring-cq-brand"
								bind:value={text_inputs[index]}
							/>
						{/each}
						<BrownButton
							onclick={submit_text_answer}
							disabled={loading || !has_text_answer}>{$t('words.submit')}</BrownButton
						>
					</div>
				{:else if current_question.type === QuizQuestionType.ORDER}
					{@const answers = current_question.answers as OrderQuizAnswer[]}
					<div class="flex flex-col gap-3">
						{#each answers as answer, index (answer.id)}
							<div
								class="cq-surface-muted flex flex-col gap-2 p-3"
								animate:flip={{ duration: 100 }}
							>
								<p
									class="notranslate text-center text-xl font-semibold text-cq-text"
									translate="no"
								>
									{answer.answer}
								</p>
								<div class="grid grid-cols-2 gap-2">
									<GrayButton
										disabled={index === 0}
										onclick={() => {
											current_question.answers = swap_array_elements(
												current_question.answers as OrderQuizAnswer[],
												index,
												index - 1
											);
										}}
									>
										{$t('solo_page.move_up')}
									</GrayButton>
									<GrayButton
										disabled={index === current_question.answers.length - 1}
										onclick={() => {
											current_question.answers = swap_array_elements(
												current_question.answers as OrderQuizAnswer[],
												index,
												index + 1
											);
										}}
									>
										{$t('solo_page.move_down')}
									</GrayButton>
								</div>
							</div>
						{/each}
						<BrownButton onclick={submit_order_answer} disabled={loading}
							>{$t('solo_page.submit_order')}</BrownButton
						>
					</div>
				{:else if current_question.type === QuizQuestionType.VOTING}
					{@const answers = current_question.answers as Answer[]}
					<div class="grid gap-3 md:grid-cols-2">
						{#each answers as answer, index (index)}
							<button
								type="button"
								class="cq-surface-muted cq-card-interactive notranslate p-4 text-center text-cq-text disabled:opacity-60"
								translate="no"
								onclick={() => submit_answer(answer.answer)}
								disabled={loading}
							>
								{answer.answer}
							</button>
						{/each}
					</div>
				{:else if current_question.type === QuizQuestionType.SLIDE}
					<div class="notranslate flex flex-col gap-4" translate="no">
						{#await import('$lib/play/admin/slide.svelte')}
							<Spinner my_20={false} />
						{:then slide}
							<div class="mx-auto max-h-[70vh] max-w-full overflow-hidden">
								<slide.default question={current_question} />
							</div>
						{/await}
						<BrownButton onclick={() => submit_answer()} disabled={loading}
							>{$t('words.continue')}</BrownButton
						>
					</div>
				{/if}

				{#if error_message}
					<p class="cq-surface-muted p-3 text-center text-cq-text" role="alert">
						{error_message}
					</p>
				{/if}
			</section>
		</div>
		{/key}
	{/if}
</div>
