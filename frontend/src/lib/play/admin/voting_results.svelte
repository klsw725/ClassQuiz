<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import type { Answer, Question, VotingAnswer } from '$lib/quiz_types';
	import { QuizQuestionType } from '$lib/quiz_types';

	interface AnswerDetail {
		answer: string;
		matched: boolean;
	}

	interface ResultAnswer {
		answer: string;
		answer_details?: AnswerDetail[];
	}

	interface AnswerBar {
		answer: string;
		count: number;
		color?: string;
		right: boolean;
	}

	interface Props {
		data: unknown;
		question: Question;
	}

	let { data, question }: Props = $props();

	let uses_submitted_answers = $derived(
		[QuizQuestionType.TEXT, QuizQuestionType.MULTI_TEXT].includes(question.type)
	);
	let show_correctness = $derived(question.type === QuizQuestionType.ABCD);
	let data_items = $derived(Array.isArray(data) ? (data as ResultAnswer[]) : []);
	let answer_counts = $derived.by((): Array<{ answer: string; count: number }> => {
		const counts: Array<{ answer: string; count: number }> = [];
		for (const result of data_items) {
			if (uses_submitted_answers && result.answer.trim() === '') {
				continue;
			}
			const answer_count = counts.find((count) => count.answer === result.answer);
			if (answer_count) {
				answer_count.count += 1;
			} else {
				counts.push({ answer: result.answer, count: 1 });
			}
		}
		return counts;
	});
	let answer_bars = $derived.by((): AnswerBar[] => {
		if (uses_submitted_answers) {
			return answer_counts
				.map((answer_count) => ({
					...answer_count,
					right: false
				}))
				.sort((a, b) => b.count - a.count);
		}

		const answer_options = Array.isArray(question.answers)
			? (question.answers as Array<Answer | VotingAnswer>)
			: [];
		return answer_options.map((answer) => ({
			answer: answer.answer,
			count: answer_counts.find((count) => count.answer === answer.answer)?.count ?? 0,
			color: answer.color,
			right: answer.right ?? false
		}));
	});
	let total_answer_count = $derived(
		uses_submitted_answers
			? answer_counts.reduce((total, answer_count) => total + answer_count.count, 0)
			: data_items.length
	);
	let multi_text_answer_details = $derived(
		question.type === QuizQuestionType.MULTI_TEXT
			? data_items.flatMap((result) => result.answer_details ?? [])
			: []
	);

	const get_bar_height = (count: number): number =>
		total_answer_count === 0 ? 0 : (count * 24) / total_answer_count;
</script>

<div class="flex justify-center w-full overflow-x-auto px-2 pb-12">
	<div
		class="cq-card m-auto w-fit gap-6 p-6 md:gap-8 md:p-8 flex flex-col"
		style="grid-template-columns: repeat({answer_bars.length}, minmax(0, 1fr));"
	>
		<div class="flex gap-8 sm:gap-12 lg:gap-16">
			{#each answer_bars as answer_bar, i (i)}
				<span class="text-center self-end mx-auto text-2xl font-semibold md:text-4xl"
					>{#if answer_bar.count > 0}{answer_bar.count}{/if}</span
				>
			{/each}
		</div>
		<div class="flex gap-8 sm:gap-12 lg:gap-16">
			{#each answer_bars as answer_bar, i (i)}
				<div
					class="cq-surface w-24 self-end flex justify-center rounded-t-lg border-2 border-cq-border shadow-2xl sm:w-28 lg:w-32"
					class:shadow-blue-500={show_correctness && answer_bar.right}
					class:shadow-yellow-500={show_correctness && !answer_bar.right}
					class:opacity-70={show_correctness && !answer_bar.right}
					style="height: {get_bar_height(
						answer_bar.count
					)}rem; background-color: {answer_bar.color
						? answer_bar.color
						: 'var(--cq-accent)'}"
				></div>
			{/each}
		</div>
		<div class="flex gap-8 sm:gap-12 lg:gap-16">
			{#each answer_bars as answer_bar, i (i)}
				<div class="w-24 sm:w-28 lg:w-32">
					<p
						class="cq-surface-muted -rotate-45 rounded-lg px-3 py-2 text-2xl md:text-3xl text-str notranslate"
						translate="no"
						class:line-through={show_correctness && !answer_bar.right}
					>
						{#if uses_submitted_answers}
							{answer_bar.answer}
						{:else}
							<!-- eslint-disable-next-line svelte/no-at-html-tags -->
							{@html answer_bar.answer}
						{/if}
					</p>
				</div>
			{/each}
		</div>
		{#if multi_text_answer_details.length}
			<div class="cq-surface-muted flex flex-col gap-2 p-3 text-left">
				{#each multi_text_answer_details as detail, index (index)}
					<div class="cq-surface flex items-center justify-between gap-3 p-2 text-sm">
						<span class="notranslate break-words text-cq-text" translate="no">
							{detail.answer || '-'}
						</span>
						<span
							class="shrink-0 font-semibold"
							class:text-cq-brand={detail.matched}
							class:text-cq-accent={!detail.matched}
						>
							{#if detail.matched}✅{:else}❌{/if}
						</span>
					</div>
				{/each}
			</div>
		{/if}
	</div>
</div>
