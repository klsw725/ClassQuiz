<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import type {
		Answer,
		OrderQuizAnswer,
		Question,
		RangeQuizAnswer,
		TextQuizAnswer
	} from '$lib/quiz_types';
	import { QuizQuestionType } from '$lib/quiz_types';
	import { socket } from '$lib/socket';
	import Spinner from '../Spinner.svelte';
	import { getLocalization } from '$lib/i18n';
	import { kahoot_icons } from './kahoot_mode_assets/kahoot_icons';
	import CircularTimer from '$lib/play/circular_progress.svelte';
	import { flip } from 'svelte/animate';
	import { tick } from 'svelte';
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
	let question_title_element = $state<HTMLHeadingElement>();
	let normal_mobile_answer_grid_element = $state<HTMLDivElement>();
	let normal_mobile_question_title_size = $state(2.75);

	interface NormalMobileAnswerTextFitOptions {
		enabled: boolean;
		text: string;
	}

	const normal_mobile_question_title_max_size = 2.75;
	const normal_mobile_question_title_min_size = 1.75;
	const normal_mobile_question_title_step = 0.05;
	const normal_mobile_answer_text_max_size = 1.5;
	const normal_mobile_answer_text_min_size = 1.125;
	const normal_mobile_answer_text_step = 0.05;
	const normal_mobile_answer_text_dynamic_max_size = 2;

	const parse_css_px = (value: string): number => {
		const parsed_value = parseFloat(value);
		return Number.isFinite(parsed_value) ? parsed_value : 0;
	};

	const normal_mobile_question_title_overflows = (
		element: HTMLHeadingElement,
		question_area: HTMLElement
	): boolean => {
		const title_styles = getComputedStyle(element);
		const question_area_styles = getComputedStyle(question_area);
		const title_vertical_margin =
			parseFloat(title_styles.marginTop) + parseFloat(title_styles.marginBottom);
		const question_area_vertical_padding =
			parseFloat(question_area_styles.paddingTop) +
			parseFloat(question_area_styles.paddingBottom);
		const available_height = question_area.clientHeight - question_area_vertical_padding;
		const rendered_height = element.getBoundingClientRect().height + title_vertical_margin;

		return (
			rendered_height > available_height + 1 ||
			element.scrollHeight > element.clientHeight + 1 ||
			element.scrollWidth > element.clientWidth + 1
		);
	};

	const update_normal_mobile_question_title_size = (element: HTMLHeadingElement) => {
		const question_area = element.parentElement;
		if (!question_area) {
			return;
		}

		let next_size = normal_mobile_question_title_max_size;
		element.style.setProperty('--normal-mobile-question-title-size', `${next_size}rem`);

		while (
			next_size > normal_mobile_question_title_min_size &&
			normal_mobile_question_title_overflows(element, question_area)
		) {
			next_size = Math.max(
				normal_mobile_question_title_min_size,
				Number((next_size - normal_mobile_question_title_step).toFixed(2))
			);
			element.style.setProperty('--normal-mobile-question-title-size', `${next_size}rem`);
		}

		normal_mobile_question_title_size = next_size;
	};

	const normal_mobile_answer_text_overflows = (element: HTMLParagraphElement): boolean => {
		const answer_content = element.parentElement;

		return (
			element.scrollHeight > element.clientHeight + 1 ||
			element.scrollWidth > element.clientWidth + 1 ||
			(answer_content !== null &&
				(answer_content.scrollHeight > answer_content.clientHeight + 1 ||
					answer_content.scrollWidth > answer_content.clientWidth + 1))
		);
	};

	const get_normal_mobile_answer_text_max_size = (element: HTMLParagraphElement): number => {
		const answer_content = element.parentElement;
		const root_font_size = parse_css_px(getComputedStyle(document.documentElement).fontSize);

		if (!answer_content || root_font_size === 0) {
			return normal_mobile_answer_text_max_size;
		}

		const content_height_rem = answer_content.clientHeight / root_font_size;
		const dynamic_max_size = content_height_rem / 5;

		return Math.min(
			normal_mobile_answer_text_dynamic_max_size,
			Math.max(normal_mobile_answer_text_max_size, dynamic_max_size)
		);
	};

	const update_normal_mobile_answer_text_size = (element: HTMLParagraphElement) => {
		let next_size = get_normal_mobile_answer_text_max_size(element);
		element.style.setProperty('--normal-mobile-answer-text-size', `${next_size}rem`);

		while (
			next_size > normal_mobile_answer_text_min_size &&
			normal_mobile_answer_text_overflows(element)
		) {
			next_size = Math.max(
				normal_mobile_answer_text_min_size,
				Number((next_size - normal_mobile_answer_text_step).toFixed(2))
			);
			element.style.setProperty('--normal-mobile-answer-text-size', `${next_size}rem`);
		}
	};

	const fit_normal_mobile_answer_text = (
		element: HTMLParagraphElement,
		options: NormalMobileAnswerTextFitOptions
	) => {
		let disposed = false;
		let animation_frame: number | undefined;
		let current_options = options;
		const mobile_query = window.matchMedia('(max-width: 639px)');
		const answer_content = element.parentElement;
		const answer_button = answer_content?.parentElement;

		const reset_size = () => {
			element.style.setProperty(
				'--normal-mobile-answer-text-size',
				`${get_normal_mobile_answer_text_max_size(element)}rem`
			);
		};

		const schedule_update = async () => {
			await tick();
			if (disposed) {
				return;
			}
			if (animation_frame !== undefined) {
				cancelAnimationFrame(animation_frame);
			}
			animation_frame = requestAnimationFrame(() => {
				if (disposed) {
					return;
				}
				if (!current_options.enabled || !mobile_query.matches) {
					reset_size();
					return;
				}
				update_normal_mobile_answer_text_size(element);
			});
		};

		const resize_observer = new ResizeObserver(schedule_update);
		resize_observer.observe(element);
		if (answer_content) {
			resize_observer.observe(answer_content);
		}
		if (answer_button) {
			resize_observer.observe(answer_button);
		}
		mobile_query.addEventListener('change', schedule_update);
		schedule_update();

		return {
			update(next_options: NormalMobileAnswerTextFitOptions) {
				current_options = next_options;
				schedule_update();
			},
			destroy() {
				disposed = true;
				resize_observer.disconnect();
				mobile_query.removeEventListener('change', schedule_update);
				if (animation_frame !== undefined) {
					cancelAnimationFrame(animation_frame);
				}
			}
		};
	};

	const update_normal_mobile_answer_grid_size = (element: HTMLDivElement) => {
		const grid_styles = getComputedStyle(element);
		const horizontal_padding =
			parse_css_px(grid_styles.paddingLeft) + parse_css_px(grid_styles.paddingRight);
		const vertical_padding =
			parse_css_px(grid_styles.paddingTop) + parse_css_px(grid_styles.paddingBottom);
		const available_width =
			element.clientWidth - horizontal_padding - parse_css_px(grid_styles.columnGap);
		const available_height =
			element.clientHeight - vertical_padding - parse_css_px(grid_styles.rowGap);
		const answer_size = Math.floor(Math.min(available_width / 2, available_height / 2));

		if (answer_size <= 0) {
			element.style.removeProperty('--normal-mobile-answer-size');
			return;
		}

		element.style.setProperty('--normal-mobile-answer-size', `${answer_size}px`);
	};

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

	$effect(() => {
		question.question;

		const element = question_title_element;
		const is_normal_mobile_question_title =
			solution === undefined && game_mode === 'normal' && !question.image;

		if (!element || !is_normal_mobile_question_title) {
			normal_mobile_question_title_size = normal_mobile_question_title_max_size;
			return;
		}

		let disposed = false;
		let animation_frame: number | undefined;
		const mobile_query = window.matchMedia('(max-width: 639px)');
		const question_area = element.parentElement;

		if (!question_area) {
			return;
		}

		const schedule_update = async () => {
			await tick();
			if (disposed) {
				return;
			}
			if (animation_frame !== undefined) {
				cancelAnimationFrame(animation_frame);
			}
			animation_frame = requestAnimationFrame(() => {
				if (disposed) {
					return;
				}
				if (!mobile_query.matches) {
					normal_mobile_question_title_size = normal_mobile_question_title_max_size;
					return;
				}
				update_normal_mobile_question_title_size(element);
			});
		};

		const resize_observer = new ResizeObserver(schedule_update);
		resize_observer.observe(question_area);
		mobile_query.addEventListener('change', schedule_update);
		schedule_update();

		return () => {
			disposed = true;
			resize_observer.disconnect();
			mobile_query.removeEventListener('change', schedule_update);
			if (animation_frame !== undefined) {
				cancelAnimationFrame(animation_frame);
			}
		};
	});

	$effect(() => {
		question.type;
		question.image;
		game_mode;
		solution;

		const element = normal_mobile_answer_grid_element;
		const is_normal_mobile_answer_grid =
			solution === undefined &&
			game_mode === 'normal' &&
			!question.image &&
			(question.type === QuizQuestionType.ABCD || question.type === QuizQuestionType.VOTING);

		if (!element || !is_normal_mobile_answer_grid) {
			return;
		}

		let disposed = false;
		let animation_frame: number | undefined;
		const mobile_query = window.matchMedia('(max-width: 639px)');
		const answer_area = element.parentElement;

		const schedule_update = async () => {
			await tick();
			if (disposed) {
				return;
			}
			if (animation_frame !== undefined) {
				cancelAnimationFrame(animation_frame);
			}
			animation_frame = requestAnimationFrame(() => {
				if (disposed) {
					return;
				}
				if (!mobile_query.matches) {
					element.style.removeProperty('--normal-mobile-answer-size');
					return;
				}
				update_normal_mobile_answer_grid_size(element);
			});
		};

		const resize_observer = new ResizeObserver(schedule_update);
		resize_observer.observe(element);
		if (answer_area) {
			resize_observer.observe(answer_area);
		}
		mobile_query.addEventListener('change', schedule_update);
		schedule_update();

		return () => {
			disposed = true;
			resize_observer.disconnect();
			mobile_query.removeEventListener('change', schedule_update);
			if (animation_frame !== undefined) {
				cancelAnimationFrame(animation_frame);
			}
		};
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

	let text_inputs = $state<string[]>([]);

	const text_answer_count = $derived.by(() => {
		if (question.type !== QuizQuestionType.MULTI_TEXT || !Array.isArray(question.answers)) {
			return 1;
		}
		return Math.max((question.answers as TextQuizAnswer[]).length, 1);
	});

	$effect(() => {
		if (
			question.type !== QuizQuestionType.TEXT &&
			question.type !== QuizQuestionType.MULTI_TEXT
		) {
			return;
		}
		if (text_inputs.length === text_answer_count) {
			return;
		}
		text_inputs = Array.from(
			{ length: text_answer_count },
			(_, index) => text_inputs[index] ?? ''
		);
	});

	let has_text_answer = $derived(text_inputs.some((answer) => answer.trim().length > 0));

	const submit_text_answer = () => {
		const answer =
			question.type === QuizQuestionType.MULTI_TEXT
				? text_inputs.join(', ')
				: (text_inputs[0] ?? '');
		const payload: {
			question_index: string | number;
			answer: string;
			complex_answer?: { answer: string }[];
		} = {
			question_index: question_index,
			answer
		};
		if (question.type === QuizQuestionType.MULTI_TEXT) {
			payload.complex_answer = text_inputs.map((answer) => ({ answer }));
		}
		selected_answer = answer;
		answer_submitted = true;
		socket.emit('submit_answer', payload);
	};

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

		if (
			solution_type === QuizQuestionType.TEXT ||
			solution_type === QuizQuestionType.MULTI_TEXT
		) {
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
		solution !== undefined &&
			(solution.type ?? QuizQuestionType.ABCD) === QuizQuestionType.VOTING
	);

	const default_colors = ['#D6EDC9', '#B07156', '#7F7057', '#4E6E58'];
</script>

<div
	class="h-screen w-screen"
	class:normal-mobile-play-screen={solution === undefined && game_mode === 'normal'}
>
	{#if solution !== undefined || game_mode === 'normal' || (game_mode === 'kahoot' && question.image)}
		<div
			class="question-area flex flex-col justify-start"
			class:normal-mobile-question={solution === undefined &&
				game_mode === 'normal' &&
				!question.image &&
				[
					QuizQuestionType.ABCD,
					QuizQuestionType.VOTING,
					QuizQuestionType.CHECK,
					QuizQuestionType.RANGE,
					QuizQuestionType.ORDER,
					QuizQuestionType.TEXT,
					QuizQuestionType.MULTI_TEXT
				].includes(question.type)}
			class:normal-mobile-question-offset={solution === undefined &&
				game_mode === 'normal' &&
				[
					QuizQuestionType.RANGE,
					QuizQuestionType.ORDER,
					QuizQuestionType.TEXT,
					QuizQuestionType.MULTI_TEXT
				].includes(question.type)}
			class:normal-mobile-question-answer-clearance={solution === undefined &&
				game_mode === 'normal' &&
				!question.image &&
				[QuizQuestionType.ABCD, QuizQuestionType.VOTING, QuizQuestionType.CHECK].includes(
					question.type
				)}
			style="--question-area-height: {get_question_area_height()}%"
		>
			<div
				bind:this={question_title_element}
				class="question-title lg:text-2xl text-lg text-left text-cq-text mt-2 break-normal mb-2 notranslate"
				role="heading"
				aria-level="1"
				style:--normal-mobile-question-title-size={`${normal_mobile_question_title_size}rem`}
				translate="no"
			>
				{@html question.question}
			</div>
			{#if solution !== undefined}
				<section class="mx-auto flex w-full max-w-3xl flex-col gap-3 px-4 text-center">
					<p class="text-xl font-semibold tracking-wide text-cq-muted uppercase">
						{#if is_voting_reveal}
							{$t('words.voting')} {$t('words.result')}
						{:else}
							{$t('words.correct')} {$t('words.answer')}
						{/if}
					</p>
					{#if is_voting_reveal}
						<div
							class="cq-card cq-surface-muted border-2 border-cq-border p-5 text-cq-text"
						>
							<p class="text-3xl font-semibold">{$t('words.voting')}</p>
						</div>
					{:else}
						<ul
							class="flex flex-col gap-2"
							aria-label="{$t('words.correct')} {$t('words.answer')}"
						>
							{#each revealed_answers as answer, i (i)}
								<li
									class="cq-card cq-surface-muted border-2 border-cq-border px-4 py-3 text-3xl font-semibold text-cq-text notranslate"
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
			<div
				class="cq-card flex w-full max-w-md flex-col gap-3 p-6 text-center shadow-2xl md:p-8"
			>
				<p class="text-3xl font-semibold text-cq-text md:text-4xl">
					{#if answer_submitted}
						{$t('play_page.answer_submitted')}
					{:else}
						{$t('play_page.please_wait')}
					{/if}
				</p>
				<p
					class="cq-surface-muted rounded-lg border-2 border-cq-border px-5 py-4 text-xl text-cq-muted md:text-2xl"
				>
					{$t('play_page.waiting_for_results')}
				</p>
			</div>
		</section>
	{:else if timer_res !== '0'}
		{#if question.type === QuizQuestionType.ABCD || question.type === QuizQuestionType.VOTING}
			<div
				class="answer-area w-full relative h-full"
				class:normal-mobile-answer-area={game_mode === 'normal'}
				style="--answer-area-height: {get_div_height()}%"
			>
				<div
					class="cq-surface absolute top-0 bottom-0 left-0 right-0 m-auto h-fit w-fit rounded-full border-2 border-cq-border shadow-2xl z-40"
					class:normal-mobile-answer-timer={game_mode === 'normal'}
				>
					<CircularTimer text={timer_res} progress={circular_progress} color="#ef4444" />
				</div>

				<div
					bind:this={normal_mobile_answer_grid_element}
					class="grid grid-rows-2 grid-flow-col auto-cols-auto gap-2 w-full p-4 h-full"
					class:normal-mobile-answer-grid={game_mode === 'normal'}
					class:normal-mobile-answer-grid-compact={game_mode === 'normal' &&
						!question.image}
				>
					{#each question.answers as answer, i}
						<button
							class="rounded-lg h-full flex min-w-0 overflow-hidden align-middle justify-center disabled:opacity-60 p-3 border-2 border-cq-border"
							class:normal-mobile-answer-button={game_mode === 'normal'}
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
										aria-label={$t('admin_page.answer_emoji')}
										>{answer.emoji}</span
									>
								{:else}
									<img
										class="h-2/3 inline-block m-auto"
										alt={$t('admin_page.answer_icon')}
										src={kahoot_icons[i]}
									/>
								{/if}
							{:else if game_mode === 'normal'}
								<div
									class="normal-mobile-answer-content m-auto flex min-w-0 max-w-full items-center justify-center gap-3"
								>
									{#if answer.emoji}
										<span
											class="normal-mobile-answer-emoji text-4xl leading-none"
											aria-label={$t('admin_page.answer_emoji')}
											>{answer.emoji}</span
										>
									{:else if kahoot_icons[i]}
										<img
											class="normal-mobile-answer-icon h-12"
											alt={$t('admin_page.answer_icon')}
											src={kahoot_icons[i]}
										/>
									{/if}
									<p
										class="normal-mobile-answer-text min-w-0 notranslate"
										use:fit_normal_mobile_answer_text={{
											enabled: game_mode === 'normal' && !question.image,
											text: answer.answer
										}}
										translate="no"
									>
										{answer.answer}
									</p>
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
			<div
				class="answer-area w-full overflow-y-auto"
				class:normal-mobile-range-answer={game_mode === 'normal' && !question.image}
				style="--answer-area-height: {get_div_height()}%"
			>
				<div class="flex justify-center mt-2">
					<div
						class="cq-surface h-fit w-fit rounded-full border-2 border-cq-border shadow-2xl"
						class:normal-mobile-answer-timer={game_mode === 'normal'}
					>
						<CircularTimer
							text={timer_res}
							progress={circular_progress}
							color="#ef4444"
						/>
					</div>
				</div>
				{#await import('svelte-range-slider-pips')}
					<Spinner />
				{:then c}
					<div
						class:pointer-events-none={selected_answer !== undefined}
						class="mt-6 normal-mobile-range-slider"
					>
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
					<div class="flex justify-center normal-mobile-range-submit">
						<div class="w-1/2 normal-mobile-range-submit-width">
							<BrownButton onclick={() => selectAnswer(String(slider_value[0]))}
								>{$t('words.submit')}
							</BrownButton>
						</div>
					</div>
				{/await}
			</div>
		{:else if question.type === QuizQuestionType.TEXT || question.type === QuizQuestionType.MULTI_TEXT}
			<div
				class="answer-area w-full overflow-y-auto"
				class:normal-mobile-text-answer={game_mode === 'normal' && !question.image}
				style="--answer-area-height: {get_div_height()}%"
			>
				<div class="flex justify-center mt-2">
					<div
						class="cq-surface h-fit w-fit rounded-full border-2 border-cq-border shadow-2xl"
						class:normal-mobile-answer-timer={game_mode === 'normal'}
					>
						<CircularTimer
							text={timer_res}
							progress={circular_progress}
							color="#ef4444"
						/>
					</div>
				</div>
				<div class="flex justify-center mt-4 normal-mobile-text-label">
					<p class="text-cq-text">{$t('editor.enter_answer')}</p>
				</div>
				<div class="m-2 flex flex-col gap-2 normal-mobile-text-inputs">
					{#each text_inputs as _text_input, i (i)}
						<div class="flex justify-center">
							<input
								type="text"
								bind:value={text_inputs[i]}
								disabled={selected_answer !== undefined}
								class="cq-surface-muted block w-full p-2 text-center text-cq-text outline-hidden ring-2 ring-cq-border transition focus:ring-cq-brand disabled:cursor-not-allowed disabled:opacity-50"
							/>
						</div>
					{/each}
				</div>

				<div class="flex justify-center mt-2 normal-mobile-text-submit">
					<div class="w-1/3 normal-mobile-text-submit-width">
						<BrownButton
							type="button"
							disabled={selected_answer !== undefined || !has_text_answer}
							onclick={submit_text_answer}
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
			<div
				class="answer-area flex flex-col w-full overflow-y-auto gap-4 px-4 py-6"
				class:normal-mobile-order-answer={game_mode === 'normal' && !question.image}
				style="--answer-area-height: {get_div_height()}%"
			>
				<div class="flex justify-center">
					<div
						class="cq-surface h-fit w-fit rounded-full border-2 border-cq-border shadow-2xl"
						class:normal-mobile-answer-timer={game_mode === 'normal'}
					>
						<CircularTimer
							text={timer_res}
							progress={circular_progress}
							color="#ef4444"
						/>
					</div>
				</div>
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
						<p
							class="w-full text-center p-2 text-2xl text-cq-text notranslate normal-mobile-order-text"
							translate="no"
						>
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
			<div class:normal-mobile-check-answer-area={game_mode === 'normal' && !question.image}>
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
					<div
						class="flex justify-center h-[5%]"
						class:normal-mobile-check-submit={game_mode === 'normal' && !question.image}
					>
						<div
							class="w-1/2"
							class:normal-mobile-check-submit-width={game_mode === 'normal' &&
								!question.image}
						>
							<BrownButton
								type="button"
								disabled={selected_answer === undefined}
								onclick={() => selectAnswer(selected_answer)}
								>{$t('words.submit')}
							</BrownButton>
						</div>
					</div>
				{/await}
			</div>
		{/if}
	{:else if solution !== undefined}
		<section
			class="flex h-1/2 items-center justify-center px-4 text-cq-text"
			aria-live="polite"
		>
			<div
				class="cq-card flex w-full max-w-md flex-col gap-4 p-6 text-center shadow-2xl md:p-8"
			>
				<p
					class="cq-surface-muted rounded-lg border-2 border-cq-border px-5 py-4 text-3xl font-semibold text-cq-brand md:text-4xl"
				>
					{$t('words.score')}
					{$t('words.public')}
				</p>
				<p class="text-xl text-cq-muted md:text-2xl">
					{$t('words.result')} {$t('words.public')}
				</p>
			</div>
		</section>
	{/if}
</div>

<style>
	.question-area {
		height: var(--question-area-height);
	}

	.answer-area {
		height: var(--answer-area-height);
	}

	.question-title {
		white-space: pre-wrap;
		overflow-wrap: anywhere;
	}

	.question-title :global(hr) {
		width: 100%;
		margin: 0.75rem auto;
		border: 0;
		border-top: 2px solid var(--cq-border-strong);
	}

	@media (max-width: 639px) {
		.normal-mobile-play-screen {
			--normal-mobile-answer-timer-clearance: 4.125rem;
			display: flex;
			flex-direction: column;
			height: 100svh;
			overflow: hidden;
		}

		.normal-mobile-question {
			flex: 0 0 33.333svh;
			height: auto;
			max-height: 33.333svh;
			min-height: 0;
			overflow-y: auto;
			padding-inline: 0.75rem;
		}

		.normal-mobile-question-offset {
			margin-top: 0;
		}

		.normal-mobile-question-answer-clearance {
			box-sizing: border-box;
			padding-bottom: var(--normal-mobile-answer-timer-clearance);
		}

		.normal-mobile-question .question-title {
			white-space: pre-wrap;
			overflow-wrap: anywhere;
			margin-top: 0.5rem;
			margin-bottom: 0.5rem;
			font-size: var(--normal-mobile-question-title-size, 2.75rem);
			line-height: 1.15;
		}

		.normal-mobile-answer-area,
		.normal-mobile-text-answer,
		.normal-mobile-order-answer,
		.normal-mobile-range-answer,
		.normal-mobile-check-answer-area {
			flex: 1 1 0;
			height: auto;
			max-height: 66.667svh;
			min-height: 0;
			overflow: hidden;
		}

		.normal-mobile-answer-area {
			display: flex;
			flex-direction: column;
		}

		.normal-mobile-range-answer,
		.normal-mobile-check-answer-area {
			display: flex;
			flex-direction: column;
			width: 100%;
		}

		.normal-mobile-range-answer {
			justify-content: flex-start;
			gap: 1rem;
			padding: 0.75rem 0.75rem 0.75rem;
		}

		.normal-mobile-range-slider {
			margin-top: 1rem;
			padding-inline: 0.75rem;
		}

		.normal-mobile-range-answer .normal-mobile-range-slider {
			margin-top: 0;
			padding-inline: 0;
			width: 100%;
		}

		.normal-mobile-range-submit {
			margin-top: 1rem;
		}

		.normal-mobile-range-answer .normal-mobile-range-submit {
			flex: 0 0 auto;
			margin-top: 0;
		}

		.normal-mobile-range-submit-width {
			width: 100%;
			max-width: 20rem;
		}

		.normal-mobile-order-answer {
			overflow-y: auto;
			gap: 0.5rem;
			margin-top: 0;
			padding: 0.5rem 0.75rem 0.75rem;
		}

		.normal-mobile-order-text {
			overflow-wrap: anywhere;
			font-size: 1.125rem;
			line-height: 1.25;
		}

		.normal-mobile-answer-timer {
			position: relative;
			z-index: auto;
			flex: 0 0 4.125rem;
			align-self: center;
			width: 4.125rem;
			height: 4.125rem;
			top: auto;
			right: auto;
			bottom: auto;
			left: auto;
			margin: 0.5rem auto 0;
			transform: none;
		}

		.normal-mobile-answer-timer :global(#progress-circle) {
			transform: scale(0.55);
			transform-origin: top left;
		}

		.normal-mobile-answer-grid {
			grid-template-rows: minmax(0, 1fr) minmax(0, 1fr);
			flex: 1 1 0;
			gap: 0.5rem;
			height: auto;
			min-height: 0;
			padding: 0.5rem;
		}

		.normal-mobile-answer-grid-compact {
			--normal-mobile-answer-size: min(
				calc((100vw - 1.5rem) / 2),
				calc((66.667svh - 4.5rem) / 2)
			);
			align-content: center;
			grid-template-columns: repeat(2, var(--normal-mobile-answer-size));
			grid-template-rows: repeat(2, var(--normal-mobile-answer-size));
			justify-content: center;
			padding-top: 0.5rem;
		}

		.normal-mobile-answer-button {
			padding: 0.5rem;
		}

		.normal-mobile-answer-grid-compact .normal-mobile-answer-button {
			height: var(--normal-mobile-answer-size);
			width: var(--normal-mobile-answer-size);
		}

		.normal-mobile-answer-content {
			flex-direction: column;
			gap: 0.25rem;
			height: 100%;
			text-align: center;
			width: 100%;
		}

		.normal-mobile-answer-emoji {
			font-size: 1.5rem;
		}

		.normal-mobile-answer-icon {
			height: 1.75rem;
		}

		.normal-mobile-answer-text {
			flex: 1 1 auto;
			max-height: 100%;
			overflow-y: auto;
			overflow-wrap: anywhere;
			font-size: var(--normal-mobile-answer-text-size, clamp(1.125rem, 3.8vw, 1.5rem));
			line-height: 1.25;
			width: 100%;
		}

		.normal-mobile-text-answer {
			display: flex;
			flex-direction: column;
			justify-content: flex-start;
			padding: 0 0.75rem 0.75rem;
		}

		.normal-mobile-text-label {
			margin-top: 0.25rem;
		}

		.normal-mobile-text-inputs {
			flex: 0 1 auto;
			min-height: 0;
			max-height: calc(66.667svh - 6rem);
			overflow-y: auto;
			margin: 0.375rem 0 0;
		}

		.normal-mobile-text-submit {
			flex: 0 0 auto;
			margin-top: 0.375rem;
		}

		.normal-mobile-text-submit-width {
			width: 100%;
			max-width: 20rem;
		}

		.normal-mobile-check-submit {
			flex: 0 0 auto;
			height: auto;
			padding: 0 0.75rem 0.75rem;
		}

		.normal-mobile-check-submit-width {
			width: 100%;
			max-width: 20rem;
		}
	}
</style>
