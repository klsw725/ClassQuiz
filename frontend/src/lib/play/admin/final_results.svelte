<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import { onMount } from 'svelte';
	import { getLocalization } from '$lib/i18n';
	import { parseParticipantKey } from '$lib/admin';

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
	type ZoneNumber = 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11;
	type SupportedZone = `${ZoneNumber}구역`;
	const supported_zones = Array.from(
		{ length: 11 },
		(_, index) => `${index + 1}구역` as SupportedZone
	);
	type ParsedPlayerName = { zone?: SupportedZone; username: string };

	const zone_badge_backgrounds: Record<SupportedZone, string> = {
		'1구역': 'border-red-300 bg-red-100 text-red-900',
		'2구역': 'border-orange-300 bg-orange-100 text-orange-900',
		'3구역': 'border-yellow-300 bg-yellow-100 text-yellow-900',
		'4구역': 'border-lime-300 bg-lime-100 text-lime-900',
		'5구역': 'border-green-300 bg-green-100 text-green-900',
		'6구역': 'border-emerald-300 bg-emerald-100 text-emerald-900',
		'7구역': 'border-teal-300 bg-teal-100 text-teal-900',
		'8구역': 'border-sky-300 bg-sky-100 text-sky-900',
		'9구역': 'border-blue-300 bg-blue-100 text-blue-900',
		'10구역': 'border-indigo-300 bg-indigo-100 text-indigo-900',
		'11구역': 'border-pink-300 bg-pink-100 text-pink-900'
	};

	const isSupportedZone = (zone: string): zone is SupportedZone =>
		(supported_zones as readonly string[]).includes(zone);

	const parseZonePlayerName = (name: string): ParsedPlayerName => {
		const separator_index = name.indexOf('-');
		if (separator_index === -1) return { username: name };

		const zone = name.slice(0, separator_index).toLowerCase();
		const username = name.slice(separator_index + 1);
		if (!username || !isSupportedZone(zone)) return { username: name };

		return { zone, username };
	};

	const getPlayerDisplayData = (player: string): ParsedPlayerName => {
		const displayName = display_names[player];
		if (displayName) return parseZonePlayerName(displayName);
		const parsed = parseParticipantKey(player);
		return parsed.zone && isSupportedZone(parsed.zone)
			? { username: parsed.username, zone: parsed.zone }
			: { username: parsed.username };
	};
	const formatPlayerName = (player: string) => getPlayerDisplayData(player).username;
	const getPlayerZone = (player: string) => getPlayerDisplayData(player).zone;

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
		username !== undefined && username in data && current_player_index !== -1
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
			{@const player_zone = getPlayerZone(player)}
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
				{#if player_zone}
					<span class="zone-badge {zone_badge_backgrounds[player_zone]}"
						>{player_zone}</span
					>
				{/if}
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

<style>
	.zone-badge {
		display: inline-flex;
		align-items: center;
		border-width: 2px;
		border-radius: 9999px;
		padding: 0.125rem 0.5rem;
		font-size: 0.3em;
		font-weight: 700;
		line-height: 1;
		text-transform: uppercase;
		vertical-align: middle;
	}
</style>
