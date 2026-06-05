<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import { fade } from 'svelte/transition';
	import type { EditorData, TextQuizAnswer } from '$lib/quiz_types';
	import { QuizQuestionType } from '$lib/quiz_types';
	import { getLocalization } from '$lib/i18n';
	import { reach } from 'yup';
	import { TextQuestionSchema } from '$lib/yupSchemas';
	import { createTippy } from 'svelte-tippy';

	interface Props {
		selected_question: number;
		data: EditorData;
	}

	let { selected_question = $bindable(), data = $bindable() }: Props = $props();

	const { t } = getLocalization();

	const get_text_question_type = () =>
		data.questions[selected_question].type === QuizQuestionType.MULTI_TEXT
			? QuizQuestionType.MULTI_TEXT
			: QuizQuestionType.TEXT;
	let max_text_answers = $derived(get_text_question_type() === QuizQuestionType.MULTI_TEXT ? 16 : 4);

	const set_text_answers = (new_answers: TextQuizAnswer[]) => {
		answers = new_answers;
		data.questions[selected_question] = {
			...data.questions[selected_question],
			type: get_text_question_type(),
			answers
		};
	};

	const normalize_text_answers = (new_answers: TextQuizAnswer[]): TextQuizAnswer[] =>
		new_answers.map((answer) => ({
			answer: answer.answer,
			case_sensitive: answer.case_sensitive ?? false
		}));

	let answers = $state<TextQuizAnswer[]>(
		normalize_text_answers(
			Array.isArray(data.questions[selected_question].answers)
				? (data.questions[selected_question].answers as TextQuizAnswer[])
				: []
		)
	);
	set_text_answers(answers);
	data.questions[selected_question].ignore_whitespace ??= false;
	if (get_text_question_type() === QuizQuestionType.MULTI_TEXT) {
		data.questions[selected_question].multi_text_order_sensitive ??= false;
	}

	const tippy = createTippy({
		arrow: true,
		animation: 'perspective-subtle'
	});

	const get_empty_answer = (): TextQuizAnswer => {
		return {
			answer: '',
			case_sensitive: false
		};
	};
</script>

<div class="flex w-full flex-col gap-3">
	<div class="flex flex-wrap justify-center gap-2 px-10">
		<button
			class="cq-surface cq-card-interactive flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition"
			type="button"
			aria-label={$t('editor.ignore_whitespace_toggle')}
			onclick={() => {
				data.questions[selected_question].ignore_whitespace =
					!data.questions[selected_question].ignore_whitespace;
			}}
			use:tippy={{ content: $t('editor.ignore_whitespace_tooltip'), placement: 'top' }}
		>
			{#if data.questions[selected_question].ignore_whitespace}
				<svg
					class="w-5 h-5 inline-block"
					fill="none"
					stroke="currentColor"
					viewBox="0 0 24 24"
					xmlns="http://www.w3.org/2000/svg"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M4 7h8M4 12h6M4 17h8m4-5l2 2 4-4"
					/>
				</svg>
			{:else}
				<svg
					class="w-5 h-5 inline-block"
					fill="none"
					stroke="currentColor"
					viewBox="0 0 24 24"
					xmlns="http://www.w3.org/2000/svg"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M4 7h16M4 12h10M4 17h16"
					/>
				</svg>
			{/if}
			<span>
				{data.questions[selected_question].ignore_whitespace
					? $t('editor.ignore_whitespace_on')
					: $t('editor.ignore_whitespace_off')}
			</span>
		</button>
		{#if get_text_question_type() === QuizQuestionType.MULTI_TEXT}
			<button
				class="cq-surface cq-card-interactive flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition"
				type="button"
				aria-label={$t('editor.multi_text_order_sensitive_toggle')}
				onclick={() => {
					data.questions[selected_question].multi_text_order_sensitive =
						!data.questions[selected_question].multi_text_order_sensitive;
				}}
				use:tippy={{ content: $t('editor.multi_text_order_sensitive_tooltip'), placement: 'top' }}
			>
				{#if data.questions[selected_question].multi_text_order_sensitive}
					<svg
						class="w-5 h-5 inline-block"
						fill="none"
						stroke="currentColor"
						viewBox="0 0 24 24"
						xmlns="http://www.w3.org/2000/svg"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M7 7h10M7 12h10M7 17h10"
						/>
					</svg>
				{:else}
					<svg
						class="w-5 h-5 inline-block"
						fill="none"
						stroke="currentColor"
						viewBox="0 0 24 24"
						xmlns="http://www.w3.org/2000/svg"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M7 7h10M7 12h7M7 17h4"
						/>
					</svg>
				{/if}
				<span>
					{data.questions[selected_question].multi_text_order_sensitive
						? $t('editor.multi_text_order_sensitive_on')
						: $t('editor.multi_text_order_sensitive_off')}
				</span>
			</button>
		{/if}
	</div>

	<div class="grid grid-cols-2 gap-4 w-full px-10">
		{#if Array.isArray(answers)}
			{#each answers as answer, index}
				<div
					out:fade={{ duration: 150 }}
					class="p-4 rounded-lg flex justify-center w-full transition relative gap-2"
					class:cq-surface-muted={answer.answer}
					class:bg-yellow-500={!reach(TextQuestionSchema, 'answer').isValidSync(
						answer.answer
					)}
				>
					<button
						class="rounded-full absolute -top-2 -right-2 opacity-70 hover:opacity-100 transition"
						type="button"
						onclick={() => {
							answers.splice(index, 1);
							set_text_answers(answers);
						}}
					>
						<svg
							class="w-6 h-6 bg-red-500 rounded-full"
							fill="none"
							stroke="currentColor"
							viewBox="0 0 24 24"
							xmlns="http://www.w3.org/2000/svg"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
							/>
						</svg>
					</button>
					<input
						bind:value={answer.answer}
						type="text"
						class="border-b-2 border-dotted flex-1 text-center rounded-lg bg-transparent outline-hidden"
						placeholder={$t('editor.enter_answer')}
					/>
					<button
						type="button"
						aria-label="Toggle case sensitivity"
						onclick={() => {
							answer.case_sensitive = !answer.case_sensitive;
						}}
						use:tippy={{ content: 'Case sensitive?', placement: 'top' }}
					>
						{#if answer.case_sensitive}
							<svg
								class="w-6 h-6 inline-block"
								fill="none"
								stroke="currentColor"
								viewBox="0 0 24 24"
								xmlns="http://www.w3.org/2000/svg"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
								/>
							</svg>
						{:else}
							<svg
								class="w-6 h-6 inline-block"
								fill="none"
								stroke="currentColor"
								viewBox="0 0 24 24"
								xmlns="http://www.w3.org/2000/svg"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
								/>
							</svg>
						{/if}
					</button>
				</div>
			{/each}
		{/if}
		{#if answers.length < max_text_answers}
			<button
				class="cq-surface cq-card-interactive p-4 rounded-lg transition"
				type="button"
				in:fade={{ duration: 150 }}
				onclick={() => {
					set_text_answers([...answers, { ...get_empty_answer() }]);
				}}
			>
				<span class="italic text-center">{$t('editor_page.add_an_answer')}</span>
			</button>
		{/if}
	</div>
</div>
