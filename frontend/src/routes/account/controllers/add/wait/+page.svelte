<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import type { PageData } from './$types';
	import CodeDisplay from '$lib/components/controller/code.svelte';
	import Spinner from '$lib/Spinner.svelte';
	import { onMount } from 'svelte';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();
	let controller_seen = $state(false);
	let check_tick = $state(0);
	let interval;

	const check_if_controller_was_seen = async () => {
		const res = await fetch(`/api/v1/box-controller/web/controller?id=${data.id}`);
		const json = await res.json();
		controller_seen = Boolean(json.first_seen);
		if (controller_seen) {
			clearInterval(interval);
		}
	};

	onMount(async () => {
		await check_if_controller_was_seen();
		interval = setInterval(async () => {
			check_tick += 1;
			if (check_tick === 5) {
				await check_if_controller_was_seen();
				check_tick = 0;
			}
		}, 1000);
	});
</script>

<div class="flex min-h-screen w-full items-center justify-center p-4 text-cq-text">
	<div class="cq-card m-auto flex w-full max-w-2xl flex-col items-center gap-6 p-6">
		<div class="block w-full">
			<CodeDisplay code={data.code} />
		</div>
		{#if controller_seen}
			<div class="cq-surface-muted w-full p-4">
				<p class="text-center text-cq-text">Controller set up successfully!</p>
			</div>
		{:else}
			<div
				class="cq-surface-muted flex w-full flex-col justify-center gap-2 p-4 text-center text-cq-muted"
			>
				<p>Checking if controller has been connected in {5 - check_tick} seconds.</p>
				<Spinner my_20={false} />
			</div>
		{/if}
	</div>
</div>
