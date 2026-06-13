<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import { run } from 'svelte/legacy';

	import type { EditorData, VotingAnswer } from '../quiz_types';
	import { QuizQuestionType } from '../quiz_types';
	import { fade } from 'svelte/transition';
	import { reach } from 'yup';
	import { getLocalization } from '$lib/i18n';
	import { VotingQuestionSchema } from '$lib/yupSchemas';
	import { get_foreground_color } from '$lib/helpers';

	const { t } = getLocalization();

	const default_colors = ['#ff5252', '#40c4ff', '#ffd740', '#69f0ae'];
	interface Props {
		selected_question: number;
		data: EditorData;
	}

	let { selected_question = $bindable(), data = $bindable() }: Props = $props();

	const set_voting_answers = (new_answers: VotingAnswer[]) => {
		answers = new_answers;
		data.questions[selected_question] = {
			...data.questions[selected_question],
			type: QuizQuestionType.VOTING,
			answers
		};
	};

	let answers = $state<VotingAnswer[]>(
		Array.isArray(data.questions[selected_question].answers)
			? (data.questions[selected_question].answers as VotingAnswer[])
			: []
	);
	if (typeof answers[0]?.right === 'boolean') {
		answers = [];
	}
	set_voting_answers(answers);

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
	/*console.log(data.questions[selected_question].answers, 'moIn!', data.questions[selected_question].answers.length);
    onMount(() => {
        for (let i = 0; i < data.questions[selected_question].answers; i++) {
            console.log(data.questions[selected_question].answers[i], 'iterate');
            data.questions[selected_question].answers[i].right = undefined;
        }
    });*/
</script>

<div class="grid grid-rows-2 grid-flow-col auto-cols-auto gap-4 w-full px-10">
	{#if Array.isArray(answers)}
		{#each answers as answer, index}
			<div
				out:fade={{ duration: 150 }}
				class="p-4 rounded-lg flex justify-center w-full transition relative"
				class:bg-yellow-500={!reach(VotingQuestionSchema, 'answer').isValidSync(
					answer.answer
				)}
								class:cq-surface-muted={answer.answer}
			>
				<button
					class="rounded-full absolute -top-2 -right-2 opacity-70 hover:opacity-100 transition"
					type="button"
					onclick={() => {
						answers.splice(index, 1);
						set_voting_answers(answers);
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
					class="border-b-2 border-dotted w-5/6 text-center rounded-lg"
					style="background-color: {answer.color ??
						'transparent'}; color: {get_foreground_color(answer.color)}"
					placeholder={$t('editor.empty')}
				/>
				<div class="flex items-center gap-1">
					<input
						class="rounded-lg p-1 border-cq-border border"
						type="color"
						bind:value={answer.color}
						oncontextmenu={(e) => {
							e.preventDefault();
							answer.color = default_colors[index];
						}}
					/>
					<button
						type="button"
						class="action-button flex items-center justify-center p-1"
						aria-label={$t('editor_page.reset_colors')}
						title={$t('editor_page.reset_colors')}
						onclick={() => {
							answer.color = default_colors[index];
						}}
					>
						<svg
							class="h-4 w-4"
							viewBox="0 0 24 24"
							fill="none"
							stroke="currentColor"
							stroke-width="2"
							stroke-linecap="round"
							stroke-linejoin="round"
						>
							<path d="M3 2v6h6" />
							<path d="M3 13a9 9 0 1 0 3-7.7L3 8" />
						</svg>
					</button>
				</div>
			</div>
		{/each}
	{/if}
	{#if answers.length < 4}
		<button
			class="cq-surface cq-card-interactive p-4 rounded-lg transition"
			type="button"
			in:fade={{ duration: 150 }}
			onclick={() => {
				set_voting_answers([
					...answers,
					{
						answer: '',
						image: undefined,
						color: default_colors[answers.length]
					}
				]);
			}}
		>
			<span class="italic text-center">{$t('editor_page.add_an_answer')}</span>
		</button>
	{/if}
</div>
