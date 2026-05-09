<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import Editor from '$lib/editor.svelte';
	import { getLocalization } from '$lib/i18n';
	import { navbarVisible } from '$lib/stores.svelte.ts';
	import { QuizQuestionType, type EditorData, type Question } from '$lib/quiz_types';

	navbarVisible.visible = false;

	const { t } = getLocalization();

	let responseData = {
		open: false,
		data: ''
	};

	let { data } = $props();
	let { quiz_id } = $state(data);
	let quiz_data: EditorData | undefined = $state();

	type EditableQuestionResponse = Question & { type?: keyof typeof QuizQuestionType | QuizQuestionType };
	type QuizResponse = Omit<EditorData, 'questions'> & { questions: EditableQuestionResponse[] };

	const get_quiz = async (): Promise<void> => {
		const response = await fetch(`/api/v1/quiz/get/${quiz_id}`);
		if (response.status === 404) {
			throw new Error('Quiz not found');
		} else if (response.status === 200) {
			let temp_data: QuizResponse = await response.json();
			for (let i = 0; i < temp_data.questions.length; i++) {
				let question = temp_data.questions[i];
				if (question.type === undefined) {
					temp_data.questions[i].type = QuizQuestionType.ABCD;
				} else {
					temp_data.questions[i].type = QuizQuestionType[question.type as keyof typeof QuizQuestionType];
				}
			}
			temp_data.time_based_scoring ??= true;
			for (const question of temp_data.questions) question.points ??= 1000;
			quiz_data = temp_data as EditorData;
			return;
		}
	};
</script>

<svelte:head>
	<title>ClassQuiz - Edit</title>
</svelte:head>
{#await get_quiz()}
	<svg class="h-8 w-8 animate-spin mx-auto my-20" viewBox="3 3 18 18">
		<path
			class="fill-cq-text"
			d="M12 5C8.13401 5 5 8.13401 5 12C5 15.866 8.13401 19 12 19C15.866 19 19 15.866 19 12C19 8.13401 15.866 5 12 5ZM3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12Z"
		/>
		<path
			class="fill-[var(--cq-surface-muted)]"
			d="M16.9497 7.05015C14.2161 4.31648 9.78392 4.31648 7.05025 7.05015C6.65973 7.44067 6.02656 7.44067 5.63604 7.05015C5.24551 6.65962 5.24551 6.02646 5.63604 5.63593C9.15076 2.12121 14.8492 2.12121 18.364 5.63593C18.7545 6.02646 18.7545 6.65962 18.364 7.05015C17.9734 7.44067 17.3403 7.44067 16.9497 7.05015Z"
		/>
	</svg>
{:then _}
	{#if quiz_data !== undefined}
		<Editor bind:data={quiz_data} bind:quiz_id />
	{/if}
{:catch err}
	<div class="text-center">
		<h1 class="text-5xl font-bold">{err.message}</h1>
	</div>
{/await}

<div
	class="fixed z-10 inset-0 overflow-y-auto"
	aria-labelledby="modal-title"
	role="dialog"
	aria-modal="true"
	class:hidden={!responseData.open}
>
	<div
		class="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0"
	>
		<div class="fixed inset-0 bg-cq-text/50 transition-opacity" aria-hidden="true"></div>

		<span class="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true"
			>&#8203;</span
		>
		<div
			class="cq-card inline-block align-bottom text-left overflow-hidden transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full"
		>
			<div class="bg-cq-surface px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
				<div class="sm:flex sm:items-start">
					<div
						class="cq-surface-muted mx-auto shrink-0 flex items-center justify-center h-12 w-12 rounded-full sm:mx-0 sm:h-10 sm:w-10"
					>
						<!-- Heroicon name: outline/exclamation -->
						<svg
							class="w-6 h-6 text-green-600"
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
					</div>
					<div class="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left">
						<h3 class="text-lg leading-6 font-medium text-cq-text" id="modal-title">
							{$t('edit_page.success_update_title')}
						</h3>
						<div class="mt-2">
							<p class="text-sm text-cq-muted">
								{$t('edit_page.success_update_body')}
							</p>
						</div>
					</div>
				</div>
			</div>
			<div class="cq-surface-muted rounded-none border-x-0 border-b-0 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
				<button
					type="button"
					onclick={() => {
						window.location.href = '/dashboard';
					}}
					class="action-button mt-3 w-full inline-flex justify-center text-base font-medium sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
					>{$t('words.close')}
				</button>
			</div>
		</div>
	</div>
</div>
