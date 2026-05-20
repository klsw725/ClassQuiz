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
		display_names?: Record<string, string>;
	}

	let { data = $bindable(), username, show_final_results, display_names = {} }: Props = $props();
	const formatPlayerName = (player: string) => display_names[player] ?? player;

	let player_names = $derived(
		Object.keys(data).sort((a, b) => {
			const scoreA = parseFloat(data[a]) || 0;
			const scoreB = parseFloat(data[b]) || 0;
			return scoreB - scoreA;
		})
	);

	let player_count_or_five = $derived(player_names.length >= 5 ? 5 : player_names.length);
	let visible_player_names = $derived(player_names.slice(0, player_count_or_five));
	let current_player_index = $derived(
		username === undefined ? -1 : player_names.indexOf(username)
	);
	let current_player_place = $derived(current_player_index + 1);
	let show_current_player_result = $derived(
		username !== undefined &&
			username in data &&
			current_player_index !== -1
	);

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
		{#each visible_player_names as player, i (player)}
			<p
				in:fly|global={{ y: -300, delay: player_count_or_five * 1200 - (i + 1) * 1000 }}
				style="font-size: clamp(3rem, {player_count_or_five + 0.75 - i / 2}rem, 7rem)"
				class="text-center leading-tight"
			>
				{$t('play_page.final_result_rank', {
					place: i + 1,
					username: formatPlayerName(player),
					points: data[player]
				})}
			</p>
		{/each}
	</div>
	{#if show_current_player_result}
		<div class="fixed bottom-0 left-0 flex justify-center w-full px-4 mb-6">
			<div
				class="cq-card mx-auto w-full max-w-md p-6 text-cq-text shadow-2xl md:max-w-xl md:p-8"
			>
				<p
					class="cq-surface-muted rounded-lg border-2 border-cq-border p-4 text-center text-2xl font-semibold text-cq-brand md:text-4xl"
				>
					{$t('play_page.your_score', { score: data[username] })}
				</p>
				<p class="mt-4 text-center text-lg font-semibold text-cq-muted md:text-2xl">
					{$t('play_page.your_place', { place: current_player_place })}
				</p>
			</div>
		</div>
	{/if}
{/if}
