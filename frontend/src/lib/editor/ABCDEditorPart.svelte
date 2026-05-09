<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import { run, preventDefault } from 'svelte/legacy';

	import type { Answer, EditorData } from '../quiz_types';
	import { QuizQuestionType } from '../quiz_types';
	import { fade } from 'svelte/transition';
	import { reach } from 'yup';
	import { ABCDQuestionSchema } from '$lib/yupSchemas';
	import { getLocalization } from '$lib/i18n';
	import { get_foreground_color } from '$lib/helpers';

	const { t } = getLocalization();

	const default_colors = ['#D6EDC9', '#B07156', '#7F7057', '#4E6E58'];

	interface Props {
		selected_question: number;
		check_choice?: boolean;
		data: EditorData;
	}

	let { selected_question = $bindable(), check_choice = false, data = $bindable() }: Props = $props();

	const set_answer_options = (new_answers: Answer[]) => {
		answers = new_answers;
		data.questions[selected_question] = {
			...data.questions[selected_question],
			type: check_choice ? QuizQuestionType.CHECK : QuizQuestionType.ABCD,
			answers
		};
	};

	let answers = $state<Answer[]>(
		Array.isArray(data.questions[selected_question].answers)
			? (data.questions[selected_question].answers as Answer[])
			: []
	);
	set_answer_options(answers);
	const save_colors = (data_local: EditorData) => {
		if (selected_question === 0) {
			for (let i = 0; i < answers.length; i++) {
				localStorage.setItem(
					`quiz_color:${i}:${data_local.title}`,
					answers[i].color
				);
			}
		}
	};

	const get_empty_answer = (i: number): Answer => {
		return {
			answer: '',
			color: default_colors[i],
			right: false
		};
	};
	run(() => {
		save_colors(data);
	});
	const set_colors_if_unset = () => {
		for (let i = 0; i < answers.length; i++) {
			if (!answers[i].color) {
				answers[i].color = default_colors[i];
			}
		}
	};
	run(() => {
		set_colors_if_unset();
		data;
		selected_question;
	});
</script>

<div class="grid grid-rows-2 grid-flow-col auto-cols-auto gap-4 w-full px-10">
	{#if Array.isArray(answers)}
		{#each answers as answer, index}
			<div
				out:fade={{ duration: 150 }}
				class="p-4 rounded-lg flex justify-center w-full transition relative"
				class:bg-red-500={!answer.right}
				class:bg-green-500={answer.right}
				class:bg-yellow-500={!reach(ABCDQuestionSchema, 'answer').isValidSync(
					answer.answer
				)}
			>
				<button
					class="rounded-full absolute -top-2 -right-2 opacity-70 hover:opacity-100 transition"
					type="button"
					onclick={() => {
						answers.splice(index, 1);
						set_answer_options(answers);
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
					class="border-b-2 border-dotted w-5/6 text-center rounded-lg bg-transparent outline-hidden focus:shadow-2xl transition-all"
					style="background-color: {answer.color}; color: {get_foreground_color(
						answer.color
					)}"
					placeholder={$t('editor.enter_answer')}
				/>
				<button
					type="button"
					onclick={() => {
						answer.right = !answer.right;
					}}
				>
					{#if answer.right}
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
				<input
					class="rounded-lg p-1 border-cq-border border"
					type="color"
					bind:value={answer.color}
					oncontextmenu={preventDefault(() => {
						answer.color = default_colors[index];
					})}
				/>
			</div>
		{/each}
	{/if}
	{#if answers.length < 4}
		<button
			class="cq-surface cq-card-interactive p-4 rounded-lg transition"
			type="button"
			in:fade={{ duration: 150 }}
			onclick={() => {
				set_answer_options([...answers, { ...get_empty_answer(answers.length) }]);
			}}
		>
			<span class="italic text-center">{$t('editor_page.add_an_answer')}</span>
		</button>
	{/if}
</div>
