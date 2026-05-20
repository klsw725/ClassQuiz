<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import { onMount } from 'svelte';
	import Editor from '$lib/editor.svelte';
	import { getLocalization } from '$lib/i18n';
	import { navbarVisible } from '$lib/stores.svelte.ts';
	import type { Question } from '$lib/quiz_types';
	import { page } from '$app/state';

	navbarVisible.visible = false;

	const { t } = getLocalization();

	interface Data {
		public: boolean;
		title: string;
		description: string;
		questions: Question[];
		time_based_scoring: boolean;
	}

	let responseData = {
		open: false
	};

	const create_empty_data = (title: string): Data => ({
		description: '',
		public: false,
		time_based_scoring: true,
		title,
		questions: [
			/*					{
				type: QuizQuestionType.ABCD,
				question: '',
				time: '20',
				points: 1000,
				answers: [{ right: false, answer: '' }]
			}*/
		]
	});

	let data: Data = $state();
	let quiz_id = $state(null);
	onMount(() => {
		const from_localstorage = localStorage.getItem('create_game');
		let title = page.url.searchParams.get('title');
		title ??= '';
		if (from_localstorage === null) {
			data = create_empty_data(title);
		} else {
			try {
				data = JSON.parse(from_localstorage);
				data.time_based_scoring ??= true;
				for (const question of data.questions) question.points ??= 1000;
			} catch {
				localStorage.removeItem('create_game');
				data = create_empty_data(title);
			}
		}
	});
</script>

<svelte:head>
	<title>ClassQuiz - Create</title>
</svelte:head>

{#if data !== undefined}
	<Editor bind:data bind:quiz_id />
{/if}

<div
	class="fixed inset-0 z-10 overflow-y-auto text-cq-text"
	aria-labelledby="modal-title"
	role="dialog"
	aria-modal="true"
	class:hidden={!responseData.open}
>
	<div
		class="flex min-h-screen items-end justify-center px-4 pt-4 pb-20 text-center sm:block sm:p-0"
	>
		<div class="fixed inset-0 bg-black/45 dark:bg-black/65 backdrop-blur-sm transition-opacity" aria-hidden="true"></div>

		<span class="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true"
			>&#8203;</span
		>
		<div
			class="cq-card inline-block transform overflow-hidden text-left align-bottom transition-all sm:my-8 sm:w-full sm:max-w-lg sm:align-middle"
		>
			<div class="bg-cq-surface px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
				<div class="sm:flex sm:items-start">
					<div
						class="cq-surface-muted mx-auto flex h-12 w-12 shrink-0 items-center justify-center rounded-full sm:mx-0 sm:h-10 sm:w-10"
					>
						<!-- Heroicon name: outline/exclamation -->
						<svg
							class="h-6 w-6 text-green-600"
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
							{$t('create_page.success.title')}
						</h3>
						<div class="mt-2">
							<p class="text-sm text-cq-muted">{$t('create_page.success.body')}</p>
						</div>
					</div>
				</div>
			</div>
			<div class="cq-surface-muted rounded-none border-x-0 border-b-0 px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6">
				<button
					type="button"
					onclick={() => {
						window.location.href = '/dashboard';
					}}
					class="action-button mt-3 inline-flex w-full justify-center text-base font-medium sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
					>{$t('words.close')}
				</button>
			</div>
		</div>
	</div>
</div>
