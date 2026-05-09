<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import { run } from 'svelte/legacy';

	import type { EditorData, Question, RangeQuizAnswer } from '../quiz_types';
	import { QuizQuestionType } from '../quiz_types';
	import Spinner from '../Spinner.svelte';

	interface Props {
		selected_question: number;
		data: EditorData;
	}

	let { selected_question = $bindable(), data = $bindable() }: Props = $props();

	type RangeQuestion = Question & { type: QuizQuestionType.RANGE; answers: RangeQuizAnswer };

	const default_range_answer = (): RangeQuizAnswer => ({
		max: 10,
		min: 0,
		max_correct: 7,
		min_correct: 3
	});

	const set_range_answer = (answers: RangeQuizAnswer) => {
		data.questions[selected_question] = {
			...data.questions[selected_question],
			type: QuizQuestionType.RANGE,
			answers
		};
	};

	let question = data.questions[selected_question];
	if (
		question.type !== QuizQuestionType.RANGE ||
		Array.isArray(question.answers) ||
		typeof question.answers === 'string' ||
		question.answers.max === undefined ||
		question.answers.min_correct === undefined
	) {
		set_range_answer(default_range_answer());
	}

	let range_answer = (data.questions[selected_question] as RangeQuestion).answers;
	let range_arr = $state([range_answer.min_correct, range_answer.max_correct]);
	run(() => {
		range_answer.min_correct = range_arr[0];
	});
	run(() => {
		range_answer.max_correct = range_arr[1];
	});
	run(() => {
		range_answer.min = range_answer.min === null ? 0 : range_answer.min;
	});
	run(() => {
		range_answer.max = range_answer.max === null ? 0 : range_answer.max;
	});

	function sleep(ms) {
		return new Promise((resolve) => setTimeout(resolve, ms));
	}
</script>

<div class="w-full mx-8">
	<div class="flex justify-center">
		<div class="grid grid-cols-2 gap-4">
			<input
				type="number"
				class="w-16 bg-transparent rounded-lg text-lg border-2 border-cq-border p-1"
				max={range_answer.max - 2}
				bind:value={range_answer.min}
			/>
			<input
				type="number"
				class="w-16 bg-transparent rounded-lg text-lg border-2 border-cq-border p-1"
				min={range_answer.min + 2}
				bind:value={range_answer.max}
			/>
		</div>
	</div>
	<div class="w-full">
		<!--		<RangeSlider bind:value={range_arr} bind:min={answer.min} bind:max={answer.max} range={true} slider={lol} /> -->

		{#await import('svelte-range-slider-pips')}
			<Spinner my_20={false} />
		{:then c}
			{#await sleep(100)}
				<Spinner my_20={false} />
			{:then _}
				<c.default
					bind:values={range_arr}
					bind:min={range_answer.min}
					bind:max={range_answer.max}
					pips
					float
					all="label"
					range
				/>
			{/await}
		{/await}
	</div>
</div>
