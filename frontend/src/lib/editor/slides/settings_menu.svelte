<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import { fade } from 'svelte/transition';

	let { title = $bindable(), time = $bindable() } = $props();
	let time_local = $state(120);
	/*eslint no-unused-vars: ["error", { "argsIgnorePattern": "^_" }]*/
	$effect(() => {
		time = String(time_local);
	});
	if (time) {
		time_local = parseInt(time);
	}
</script>

<div
	class="cq-card m-auto p-4 h-fit gap-2 w-fit auto-cols-min flex"
	transition:fade|global={{ duration: 100 }}
>
	<label class="w-fit">
		Time
		<input
			bind:value={time}
			type="number"
			class="w-20 bg-transparent rounded-lg text-lg border-2 border-cq-border p-1 outline-hidden text-cq-text"
		/>
	</label>
	<label class="w-fit">
		Title
		<input
			bind:value={title}
			type="text"
			class="bg-transparent rounded-lg text-lg border-2 border-cq-border p-1 transition outline-hidden text-cq-text"
		/>
	</label>
</div>
