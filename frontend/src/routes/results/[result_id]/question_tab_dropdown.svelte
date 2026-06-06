<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import { QuizQuestionType } from '$lib/quiz_types';
	import { getLocalization } from '$lib/i18n';
	import type { Answer as QuizAnswer, GeneralQuizAnswer, Question } from '$lib/quiz_types';
	import { participantKey } from '$lib/admin';

	const { t } = getLocalization();
	const RESULT_TABLE_PAGE_SIZE = 100;

	interface AnswerDetail {
		answer: string;
		matched: boolean;
	}

	interface PlayerAnswer {
		username: string;
		answer: string;
		answer_details?: AnswerDetail[];
		right: boolean;
		time_taken: number;
		score: number;
		zone?: string;
	}

	interface Props {
		question: Question;
		answers: PlayerAnswer[];
	}

	let { question, answers }: Props = $props();
	let visible_answer_count = $state(RESULT_TABLE_PAGE_SIZE);
	let visible_answers = $derived(answers.slice(0, visible_answer_count));
	let hidden_answer_count = $derived(Math.max(answers.length - visible_answers.length, 0));
	let free_text_question = $derived(
		question.type === QuizQuestionType.TEXT || question.type === QuizQuestionType.MULTI_TEXT
	);
	const playerDisplayName = (answer: PlayerAnswer): string =>
		answer.zone ? `${answer.zone}-${answer.username}` : answer.username;
	const hasMultiTextAnswerDetails = (answer: PlayerAnswer): boolean =>
		question.type === QuizQuestionType.MULTI_TEXT && Boolean(answer.answer_details?.length);
	const formatScore = (score: number): string => String(score ?? 0);

	const get_answer_for_comparison = (answer: string): string => {
		if (free_text_question && question.ignore_whitespace) {
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
		const answer_for_comparison = free_text_question
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
			} else if (free_text_question) {
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
		{#if question.type !== QuizQuestionType.ORDER && question.type !== QuizQuestionType.RANGE && question.type !== QuizQuestionType.SLIDE && !free_text_question}
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
							{#if question.type !== QuizQuestionType.VOTING}
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
					{#each visible_answers as answer (participantKey(answer.username, answer.zone))}
						<tr>
							<td class="border-r p-1 border-cq-border"
								>{playerDisplayName(answer)}</td
							>
							{#if question.type !== QuizQuestionType.VOTING}
								<td class="border-r p-1 border-cq-border"
									>{formatScore(answer.score)}</td
								>
							{/if}
							<td class="border-r p-1 border-cq-border"
								>{(answer.time_taken / 1000).toFixed(3)}s
							</td>
							<td class="p-1">
								{#if hasMultiTextAnswerDetails(answer)}
									<div class="flex flex-col gap-1">
										{#each answer.answer_details ?? [] as detail, index (index)}
											<div
												class="cq-surface-muted flex items-center justify-between gap-2 p-1 text-sm"
											>
												<span
													class="notranslate break-words"
													translate="no"
												>
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
								{:else}
									{answer.answer}
								{/if}
							</td>
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
