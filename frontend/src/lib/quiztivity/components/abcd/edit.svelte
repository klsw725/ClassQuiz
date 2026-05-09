<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import type { Abcd } from '$lib/quiztivity/types';
	import { getLocalization } from '$lib/i18n';
	import BrownButton from '$lib/components/buttons/brown.svelte';

	interface Props {
		data: Abcd | undefined;
	}

	let { data = $bindable() }: Props = $props();

	if (!data) {
		data = {
			question: '',
			answers: []
		};
	}

	const { t } = getLocalization();
</script>

<div>
	<div class="flex justify-center">
		<input
			class="bg-transparent outline-hidden text-3xl text-center text-cq-text placeholder:text-cq-muted"
			placeholder="Enter question here..."
			bind:value={data.question}
		/>
	</div>
	<div class="grid grid-cols-2 m-4 gap-4">
		{#each data.answers as answer}
			<div class="cq-surface-muted p-6 flex">
				<input
					bind:value={answer.answer}
					class="w-full my-auto bg-transparent outline-hidden text-center text-cq-text placeholder:text-cq-muted"
					placeholder="Enter answer here"
				/>
				<button
					type="button"
					onclick={() => {
						answer.correct = !answer.correct;
					}}
				>
				{#if answer.correct}
					<svg
						class="w-6 h-6 inline-block text-cq-text"
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
						class="w-6 h-6 inline-block text-cq-text"
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
		{#if data.answers.length < 4}
			<div class="cq-surface-muted p-6">
				<BrownButton
					onclick={() => {
						data.answers = [...data.answers, { ...{ answer: '', correct: false } }];
					}}>{$t('editor_page.add_an_answer')}</BrownButton
				>
			</div>
		{/if}
	</div>
</div>
