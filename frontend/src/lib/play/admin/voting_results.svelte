<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import type { Answer, Question, VotingAnswer } from '$lib/quiz_types';
	import { QuizQuestionType } from '$lib/quiz_types';

	interface Props {
		data: any;
		question: Question;
	}

	let { data, question }: Props = $props();

	let quiz_answers = [];
	let quiz_colors = [];
	let answer_correct: boolean[] = [];

	const answer_options = Array.isArray(question.answers)
		? (question.answers as Array<Answer | VotingAnswer>)
		: [];
	for (const i of answer_options) {
		quiz_answers.push(i.answer);
		quiz_colors.push(i.color);
		answer_correct.push(i.right ?? false);
	}

	let sorted_data = $state({});
	for (const i of quiz_answers) {
		sorted_data[i] = 0;
	}
	for (const i of data) {
		sorted_data[i.answer] += 1;
	}
</script>

<div class="flex justify-center w-full overflow-x-auto px-2 pb-12">
	<div
		class="cq-card m-auto w-fit gap-6 p-6 md:gap-8 md:p-8 flex flex-col"
		style="grid-template-columns: repeat({quiz_answers.length}, minmax(0, 1fr));"
	>
		<div class="flex gap-8 sm:gap-12 lg:gap-16">
			{#each quiz_answers as answer}
				<span class="text-center self-end mx-auto text-2xl font-semibold md:text-4xl"
					>{#if sorted_data[answer] > 0}{sorted_data[answer]}{/if}</span
				>
			{/each}
		</div>
		<div class="flex gap-8 sm:gap-12 lg:gap-16">
			{#each quiz_answers as answer, i}
				<div
					class="cq-surface w-24 self-end flex justify-center rounded-t-lg border-2 border-cq-border shadow-2xl sm:w-28 lg:w-32"
					class:shadow-blue-500={answer_correct[i] &&
						question.type !== QuizQuestionType.VOTING}
					class:shadow-yellow-500={!answer_correct[i] &&
						question.type !== QuizQuestionType.VOTING}
					class:opacity-70={!answer_correct[i] &&
						question.type !== QuizQuestionType.VOTING}
					style="height: {(sorted_data[answer] * 24) /
						data.length}rem; background-color: {quiz_colors[i]
						? quiz_colors[i]
						: 'var(--cq-accent)'}"
				></div>
			{/each}
		</div>
		<div class="flex gap-8 sm:gap-12 lg:gap-16">
			{#each quiz_answers as answer, i}
				<div class="w-24 sm:w-28 lg:w-32">
					<p
						class="cq-surface-muted -rotate-45 rounded-lg px-3 py-2 text-2xl md:text-3xl text-str notranslate"
						translate="no"
						class:line-through={!answer_correct[i] &&
							question.type !== QuizQuestionType.VOTING}
					>
						{@html answer}
					</p>
				</div>
			{/each}
		</div>
	</div>
</div>
