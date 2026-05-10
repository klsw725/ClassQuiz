<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import { onMount } from 'svelte';
	import { getLocalization } from '$lib/i18n';

	const { t } = getLocalization();

	import { fly } from 'svelte/transition';
	import confetti from 'canvas-confetti';
	interface Props {
		data: any;
		username?: any;
		show_final_results: boolean;
	}

	let { data = $bindable(), username, show_final_results }: Props = $props();

	let player_names = $derived(Object.keys(data).sort((a, b) => {
		const scoreA = parseFloat(data[a]) || 0;
		const scoreB = parseFloat(data[b]) || 0;
		return scoreB - scoreA;
	}));

	let player_count_or_five = $derived(player_names.length >= 5 ? 5 : player_names.length);

	let canvas: HTMLCanvasElement = $state();
	onMount(() => {
		setTimeout(
			() => {
				confetti.create(canvas, {
					resize: true,
					useWorker: true
				});
				confetti({ particleCount: 200, spread: 160 });
			},
			player_count_or_five * 1200 - 800
		);
	});
</script>

{#if show_final_results}
	<canvas bind:this={canvas}></canvas>
	<div class="px-4 py-8 md:py-12">
		{#each player_names as player, i}
			{#if i <= player_count_or_five - 1}
				<p
					in:fly|global={{ y: -300, delay: player_count_or_five * 1200 - (i + 1) * 1000 }}
					style="font-size: clamp(3rem, {player_count_or_five + 0.75 - i / 2}rem, 7rem)"
					class="text-center leading-tight"
				>
					{$t('play_page.final_result_rank', {
						place: i + 1,
						username: player,
						points: data[player]
					})}
				</p>
			{/if}
		{/each}
	</div>
	{#if data[username]}
		<div class="fixed bottom-0 left-0 flex justify-center w-full px-4 mb-6">
			<div class="cq-card mx-auto w-full max-w-md p-6 text-cq-text shadow-2xl md:max-w-xl md:p-8">
				<p class="cq-surface-muted rounded-lg border-2 border-cq-border p-4 text-center text-2xl font-semibold text-cq-brand md:text-4xl">
					{$t('play_page.your_score', { score: data[username] })}
				</p>
				{#each player_names as player, i}
					{#if player === username}
						<p class="mt-4 text-center text-lg font-semibold text-cq-muted md:text-2xl">
							{$t('play_page.your_place', { place: i + 1 })}
						</p>
					{/if}
				{/each}
			</div>
		</div>
	{/if}
{/if}
