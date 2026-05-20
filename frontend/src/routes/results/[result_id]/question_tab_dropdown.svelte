<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import { QuizQuestionType } from '$lib/quiz_types';
	import { getLocalization } from '$lib/i18n';
	import type { Answer as QuizAnswer, GeneralQuizAnswer, Question } from '$lib/quiz_types';

	const { t } = getLocalization();
	const RESULT_TABLE_PAGE_SIZE = 100;

	interface PlayerAnswer {
		username: string;
		answer: string;
		right: boolean;
		time_taken: number;
		score: number;
	}

	interface Props {
		question: Question;
		answers: PlayerAnswer[];
	}

	let { question, answers }: Props = $props();
	let visible_answer_count = $state(RESULT_TABLE_PAGE_SIZE);
	let visible_answers = $derived(answers.slice(0, visible_answer_count));
	let hidden_answer_count = $derived(
		Math.max(answers.length - visible_answers.length, 0)
	);

	const get_answer_for_comparison = (answer: string): string => {
		if (question.type === QuizQuestionType.TEXT && question.ignore_whitespace) {
			return answer.replace(/\s/g, '');
		}
		return answer;
	};

	const get_text_answer_for_comparison = (
		answer: string,
		case_sensitive: boolean | undefined
	): string => {
		const answer_for_comparison = get_answer_for_comparison(answer);
		return case_sensitive ? answer_for_comparison : answer_for_comparison.toLowerCase();
	};

	const get_answer_count_for_answer = (answer: GeneralQuizAnswer): number => {
		let count = 0;
		let answer_id = 0;
		const answer_for_comparison =
			question.type === QuizQuestionType.TEXT
				? get_text_answer_for_comparison(answer.answer, answer.case_sensitive)
				: get_answer_for_comparison(answer.answer);
		if (question.type === QuizQuestionType.CHECK) {
			const answer_options = question.answers as QuizAnswer[];
			for (let i = 0; i < answer_options.length; i++) {
				if (answer.answer === answer_options[i].answer) {
					answer_id = i;
					break;
				}
			}
		}
		for (let i = 0; i < answers.length; i++) {
			const a = answers[i];
			if (question.type === QuizQuestionType.CHECK) {
				console.log(a.answer.includes('2'), answer_id);
				if (a.answer.includes(String(answer_id))) {
					count++;
				}
			} else if (question.type === QuizQuestionType.TEXT) {
				if (
					get_text_answer_for_comparison(a.answer, answer.case_sensitive) ===
					answer_for_comparison
				) {
					count++;
				}
			} else if (get_answer_for_comparison(a.answer) === answer_for_comparison) {
				count++;
			}
		}
		return count;
	};
</script>

<div class="flex justify-center">
	<div class="cq-surface-muted p-2 w-10/12">
		{#if question.type !== QuizQuestionType.ORDER && question.type !== QuizQuestionType.RANGE && question.type !== QuizQuestionType.SLIDE}
			<div class="flex flex-col mb-4">
				{#each question.answers as answer, i (i)}
					<div class="grid grid-cols-4">
						<p>{answer.answer}</p>
						<div class="col-span-3 flex w-full border-l border-cq-border px-1">
							<div class="my-auto w-full mr-1">
								<span
									class="h-1 block bg-cq-brand my-auto"
									style="width: {(get_answer_count_for_answer(answer) /
										answers.length) *
										100}%"
								></span>
							</div>
							<p>{get_answer_count_for_answer(answer)}</p>
							{#if question.type !== QuizQuestionType.VOTING && question.type !== QuizQuestionType.TEXT}
								<p class="ml-1">
									{#if answer.right}✅{:else}❌{/if}
								</p>
							{/if}
						</div>
					</div>
				{/each}
			</div>
		{/if}
		<div>
			<div class="mb-2 text-sm font-semibold text-cq-muted">
				{visible_answers.length}/{answers.length}
			</div>
			<table class="w-full text-left">
				<thead>
					<tr class="border-b-2 text-left border-cq-border">
						<th class="border-r p-1 mx-auto border-cq-border"
							>{$t('result_page.player_name')}
						</th>
						{#if question.type !== QuizQuestionType.VOTING}
							<th class="border-r p-1 mx-auto border-cq-border"
								>{$t('words.score')}</th
							>
						{/if}
						<th class="border-r p-1 mx-auto border-cq-border"
							>{$t('result_page.time_taken')}
						</th>
						<th class="p-1 mx-auto">{$t('words.answer')} </th>
						{#if question.type !== QuizQuestionType.VOTING}
							<th class="border-l p-1 mx-auto border-cq-border"
								>{$t('words.correct')}?
							</th>
						{/if}
					</tr>
				</thead>
				<tbody>
					{#each visible_answers as answer (answer.username)}
						<tr>
							<td class="border-r p-1 border-cq-border"
								>{answer.username}</td
							>
							{#if question.type !== QuizQuestionType.VOTING}
								<td class="border-r p-1 border-cq-border"
									>{answer.score}</td
								>
							{/if}
							<td class="border-r p-1 border-cq-border"
								>{(answer.time_taken / 1000).toFixed(3)}s
							</td>
							<td class="p-1">{answer.answer}</td>
							{#if question.type !== QuizQuestionType.VOTING}
								<td class="p-1 border-l border-cq-border">
									{#if answer.right}✅{:else}❌{/if}
								</td>
							{/if}
						</tr>
					{/each}
				</tbody>
			</table>
			{#if hidden_answer_count > 0}
				<button
					type="button"
					class="cq-surface w-full p-2 font-semibold text-cq-muted hover:text-cq-text transition"
					onclick={() => (visible_answer_count += RESULT_TABLE_PAGE_SIZE)}
				>
					+{Math.min(RESULT_TABLE_PAGE_SIZE, hidden_answer_count)}
				</button>
			{/if}
		</div>
	</div>
</div>
