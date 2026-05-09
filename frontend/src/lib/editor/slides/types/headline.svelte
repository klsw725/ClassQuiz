<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	interface Props {
		data: any;
		editor?: boolean;
	}

	let { data = $bindable(), editor = true }: Props = $props();
</script>

{#if editor}
	<input
		bind:value={data}
		type="text"
		class="h-full min-h-fit w-full text-center text-3xl text-black"
	/>
{:else}
	<h2 class="w-full h-full text-center text-3xl min-h-fit">
		{data}
	</h2>
{/if}
