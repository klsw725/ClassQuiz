<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import type { Abcd } from '$lib/quiztivity/types';

	interface Props {
		data: Abcd | undefined;
	}

	let { data }: Props = $props();

	let selected_answer: number | undefined = $state();

	const select_answer = (i: number) => {
		selected_answer = i;
		console.log(data);
	};
</script>

<div class="p-4 text-cq-text">
	<h1 class="cq-card mx-auto max-w-4xl p-6 text-center text-4xl font-semibold text-cq-text">{data.question}</h1>

	<div class="grid grid-cols-1 lg:grid-cols-2 m-4 gap-4">
		{#each data.answers as answer, i}
			<button
				class="cq-card cq-card-interactive p-6 flex transition-all"
				onclick={() => {
					select_answer(i);
				}}
				class:opacity-50={selected_answer !== undefined && !answer.correct}
				class:text-2xl={selected_answer === i}
			>
				<span class="m-auto text-cq-text">{answer.answer}</span>
			</button>
		{/each}
	</div>
</div>
