<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import type { Question } from '$lib/quiz_types';
	import { QuizQuestionType } from '$lib/quiz_types';
	import { onMount } from 'svelte';
	import { fade } from 'svelte/transition';
	import { getLocalization } from '$lib/i18n';


	interface Props {
		questions: Question[];
		open: boolean;
		selected_question: number;
	}

	let { questions = $bindable(), open = $bindable(), selected_question = $bindable() }: Props = $props();

	const { t } = getLocalization();
	onMount(() => {
		document.body.addEventListener('keydown', close_start_game_if_esc_is_pressed);
	});
	const close_start_game_if_esc_is_pressed = (key: KeyboardEvent) => {
		if (key.code === 'Escape') {
			open = false;
		}
	};
	const on_parent_click = (e: Event) => {
		if (e.target === e.currentTarget) {
			open = false;
		}
	};

	const question_types: {
		name: string;
		description: string;
		question: Question;
	}[] = [
		{
			name: $t('words.multiple_choice'),
			description: $t('editor.abcd_description'),
			question: {
				type: QuizQuestionType.ABCD,
				time: '20',
				points: 1000,
				question: '',
				image: undefined,
				answers: []
			}
		},
		{
			name: $t('words.voting'),
			description: $t('editor.voting_description'),
			question: {
				type: QuizQuestionType.VOTING,
				time: '20',
				points: 1000,
				question: '',
				image: undefined,
				answers: []
			}
		},
		{
			name: $t('words.check_choice'),
			description: $t('editor.check_choice_description'),
			question: {
				type: QuizQuestionType.CHECK,
				time: '20',
				points: 1000,
				question: '',
				image: undefined,
				answers: []
			}
		},
		{
			name: $t('words.order'),
			description: $t('editor.order_description'),
			question: {
				type: QuizQuestionType.ORDER,
				time: '20',
				points: 1000,
				question: '',
				image: undefined,
				answers: []
			}
		},
		{
			name: $t('words.text'),
			description: $t('editor.text_description'),
			question: {
				type: QuizQuestionType.TEXT,
				time: '20',
				points: 1000,
				question: '',
				image: undefined,
				ignore_whitespace: false,
				multi_text_order_sensitive: false,
				answers: []
			}
		},
		{
			name: $t('words.multi_text'),
			description: $t('editor.multi_text_description'),
			question: {
				type: QuizQuestionType.MULTI_TEXT,
				time: '20',
				points: 1000,
				question: '',
				image: undefined,
				ignore_whitespace: false,
				answers: []
			}
		},
		{
			name: $t('words.range'),
			description: $t('editor.range_description'),
			question: {
				type: QuizQuestionType.RANGE,
				time: '20',
				points: 1000,
				question: '',
				image: undefined,
				answers: {
					max: 10,
					min: 0,
					max_correct: 7,
					min_correct: 3
				}
			}
		}
	];

	const add_question = (index: number) => {
		const empty_question = question_types[index].question;
		questions = [...questions, { ...empty_question }];
		selected_question = questions.length - 1;
		open = false;
	};
</script>

<div
	class="fixed top-0 left-0 w-screen h-screen flex bg-cq-text/50 z-50"
	onclick={on_parent_click}
	transition:fade={{ duration: 100 }}
>
	<div
		class="cq-card m-auto w-2/3 h-5/6 p-6 flex flex-col"
	>
		<h1 class="text-center text-3xl mb-6">{$t('quiztivity.editor.select_page_type')}</h1>
		<div class="grid grid-cols-4 gap-4 overflow-y-scroll">
			{#each question_types as qt, i}
				<div class="cq-card cq-card-interactive p-6">
					<button
						class="text-xl text-cq-text"
						onclick={() => {
							add_question(i);
						}}>{qt.name}</button
					>
					<p class="text-sm text-cq-muted">{qt.description}</p>
				</div>
			{/each}
		</div>

		<div class="mt-auto flex justify-center">
			<p>
				{$t('editor.need_more_help')}
				<a
					href="/docs/quiz/question-types"
					target="_blank"
					class="text-sm font-bold underline link-hover"
					>{$t('editor.visit_docs')}</a
				>
			</p>
		</div>
	</div>
</div>
