<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	let color_map = {
		r: 'red',
		g: 'green',
		y: 'yellow',
		b: 'blue'
	};
	interface Props {
		code: string;
	}

	let { code }: Props = $props();
</script>

<div class="cq-card mx-auto flex flex-row justify-center gap-3 p-4">
	{#each code as c}
		<div class="cq-surface-muted flex flex-col items-center gap-2 p-2">
			<p class="text-center font-mono text-cq-text">{c}</p>
			<span
				style="background-color: {color_map[
					c.toLowerCase()
				]}; width: 2rem; height: {c.toLowerCase() == c ? '2' : '4'}rem"
			></span>
		</div>
	{/each}
</div>
