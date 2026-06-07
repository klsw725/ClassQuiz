<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import { QuizQuestionType } from '$lib/quiz_types';
	import type {
		QuizData,
		OrderQuizAnswer,
		RangeQuizAnswer,
		TextQuizAnswer
	} from '$lib/quiz_types';
	import { get_foreground_color } from '$lib/helpers.js';
	import { kahoot_icons } from '$lib/play/kahoot_mode_assets/kahoot_icons.js';
	import CircularTimer from '$lib/play/circular_progress.svelte';
	import MediaComponent from '$lib/editor/MediaComponent.svelte';
	import { getLocalization } from '$lib/i18n';

	interface Props {
		quiz_data: QuizData;
		selected_question: number;
		timer_res: string;
		answer_count: number;
		default_colors: string[];
	}

	let {
		quiz_data,
		selected_question,
		timer_res = $bindable(),
		answer_count,
		default_colors
	}: Props = $props();

	const { t } = getLocalization();

	let current_question = $derived(quiz_data.questions[selected_question]);
	let reveal = $derived(timer_res === '0');
	let is_mcq = $derived(
		current_question.type === QuizQuestionType.ABCD ||
			current_question.type === QuizQuestionType.CHECK
	);

	let is_text_reveal = $derived(
		current_question.type === QuizQuestionType.TEXT ||
			current_question.type === QuizQuestionType.MULTI_TEXT
	);

	let centered_reveal_lines = $derived.by((): string[] => {
		if (!reveal) return [];
		const q = current_question;
		if (q.type === QuizQuestionType.RANGE) {
			const r = q.answers as RangeQuizAnswer;
			return [`${r.min_correct} ~ ${r.max_correct}`];
		}
		if (q.type === QuizQuestionType.ORDER) {
			return (q.answers as OrderQuizAnswer[]).map((a) => a.answer);
		}
		if (q.type === QuizQuestionType.TEXT || q.type === QuizQuestionType.MULTI_TEXT) {
			return (q.answers as TextQuizAnswer[]).map((a) => a.answer);
		}
		return [];
	});

	let circular_progress = $derived.by(() => {
		try {
			return (
				1 -
				((100 / parseInt(quiz_data.questions[selected_question].time)) *
					parseInt(timer_res)) /
					100
			);
		} catch {
			return 0;
		}
	});
</script>

<div class="flex flex-col justify-center w-screen h-1/6">
	<div
		class="question-title text-6xl text-left notranslate"
		role="heading"
		aria-level="1"
		translate="no"
	>
		{@html quiz_data.questions[selected_question].question}
	</div>
	<!--			<span class='text-center py-2 text-lg'>{$t('admin_page.time_left')}: {timer_res}</span>-->
	<div class="grid grid-cols-3 my-2">
		<span></span>
		<div class="m-auto">
			<CircularTimer text={timer_res} progress={circular_progress} color="#ef4444" />
		</div>
		<p class="m-auto text-3xl">
			{$t('admin_page.answers_submitted', { answer_count: answer_count })}
		</p>
	</div>
</div>
{#if quiz_data.questions[selected_question].image !== null}
	<div class="flex w-full">
		<MediaComponent
			src={quiz_data.questions[selected_question].image}
			muted={false}
			css_classes="max-h-[20vh] object-cover mx-auto mb-8 w-auto"
		/>
	</div>
{/if}

<style>
	.question-title :global(hr) {
		width: 100%;
		margin: 0.75rem auto;
		border: 0;
		border-top: 2px solid var(--cq-border-strong);
	}

	.correct-reveal {
		border-color: #10b981;
		box-shadow: 0 0 0 4px rgba(16, 185, 129, 0.25), 0 12px 28px rgba(16, 185, 129, 0.35);
		transform: scale(1.03);
		z-index: 1;
	}

	.correct-check {
		color: #047857;
		text-shadow: 0 2px 6px rgba(255, 255, 255, 0.8);
	}

	.correct-reveal-card {
		border: 4px solid #10b981;
		box-shadow: 0 0 0 6px rgba(16, 185, 129, 0.2), 0 24px 48px rgba(16, 185, 129, 0.25);
	}
</style>
{#if current_question.type === QuizQuestionType.ABCD || current_question.type === QuizQuestionType.VOTING || current_question.type === QuizQuestionType.CHECK}
	<div class="grid grid-rows-2 grid-flow-col auto-cols-auto gap-2 w-full p-4">
		{#each current_question.answers as answer, i}
			{@const mcq_reveal = reveal && is_mcq}
			{@const is_correct = answer.right === true}
			<div
				class="rounded-lg h-fit flex relative transition-all duration-200"
				class:border-2={!(mcq_reveal && is_correct)}
				class:border-cq-border={!(mcq_reveal && is_correct)}
				class:border-4={mcq_reveal && is_correct}
				class:correct-reveal={mcq_reveal && is_correct}
				class:opacity-40={mcq_reveal && !is_correct}
				style="background-color: {answer.color ?? default_colors[i]};"
			>
				{#if answer.emoji}
					<span class="w-14 pl-4 text-4xl leading-none" aria-label={$t('admin_page.answer_emoji')}
						>{answer.emoji}</span
					>
				{:else}
					<img
						class="w-14 inline-block pl-4"
						alt={$t('admin_page.answer_icon')}
						style="color: {get_foreground_color(answer.color ?? default_colors[i])}"
						src={kahoot_icons[i]}
					/>
				{/if}
				<span
					class="text-center text-2xl px-2 py-4 w-full notranslate"
					translate="no"
					style="color: {get_foreground_color(answer.color ?? default_colors[i])}"
					>{answer.answer}</span
				>
				{#if mcq_reveal && is_correct}
					<span
						class="correct-check w-14 flex items-center justify-center text-5xl font-black"
						aria-label={$t('words.correct')}
					>
						✓
					</span>
				{:else}
					<span class="pl-4 w-10"></span>
				{/if}
			</div>
		{/each}
	</div>
{:else if reveal && (current_question.type === QuizQuestionType.TEXT || current_question.type === QuizQuestionType.MULTI_TEXT || current_question.type === QuizQuestionType.RANGE || current_question.type === QuizQuestionType.ORDER)}
	<div class="flex justify-center items-center px-6 py-10" style="min-height: 60vh;">
		<div
			class="cq-card max-w-4xl w-full text-center px-10 py-12 shadow-2xl correct-reveal-card"
		>
			<p class="text-2xl md:text-3xl font-semibold tracking-widest text-cq-muted uppercase mb-6">
				{$t('words.correct')}
			</p>
			<ul class="flex flex-col gap-4" class:text-left={is_text_reveal}>
				{#each centered_reveal_lines as line, i (i)}
					<li
						class="text-5xl md:text-6xl font-bold text-cq-text notranslate break-words"
						translate="no"
					>
						{line}
					</li>
				{/each}
			</ul>
		</div>
	</div>
{:else if current_question.type === QuizQuestionType.TEXT || current_question.type === QuizQuestionType.MULTI_TEXT}
	<div class="flex justify-center">
		<p class="text-2xl">{$t('admin_page.enter_answer_into_field')}</p>
	</div>
{/if}
