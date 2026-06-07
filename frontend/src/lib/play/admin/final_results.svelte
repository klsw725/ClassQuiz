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

	let zone_rankings = $derived.by(() => {
		const totals: Record<string, { score: number; players: number }> = {};
		for (const player of player_names) {
			const zone = getPlayerZone(player);
			if (!zone) continue;
			if (!totals[zone]) totals[zone] = { score: 0, players: 0 };
			totals[zone].score += parseFloat(data[player]) || 0;
			totals[zone].players += 1;
		}
		return Object.entries(totals)
			.map(([zone, value]) => ({ zone, ...value }))
			.sort((a, b) => b.score - a.score);
	});
	let has_zone_rankings = $derived(zone_rankings.length > 0);

	let visible_player_count = $derived(
		Math.min(player_names.length, has_zone_rankings ? 5 : 10)
	);
	let visible_player_names = $derived(player_names.slice(0, visible_player_count));
	let visible_zone_count = $derived(zone_rankings.length);
	let current_player_index = $derived(
		username === undefined ? -1 : player_names.indexOf(username)
	);
	let current_player_place = $derived(current_player_index + 1);
	let show_current_player_result = $derived(
		username !== undefined && username in data && current_player_index !== -1
	);

	let canvas: HTMLCanvasElement = $state();
	let confetti_delay = $derived(
		Math.max(visible_player_count, visible_zone_count) * 800 - 400
	);
	onMount(() => {
		setTimeout(() => {
			confetti.create(canvas, {
				resize: true,
				useWorker: true
			});
			confetti({ particleCount: 200, spread: 160 });
		}, confetti_delay);
	});
</script>

{#if show_final_results}
	<canvas bind:this={canvas}></canvas>
	<div
		class="results-layout px-4 py-8 md:py-12"
		class:has-zones={has_zone_rankings}
	>
		{#if has_zone_rankings}
			<section class="zone-column">
				<h2
					in:fly|global={{ y: -120, delay: 0 }}
					class="mb-6 text-center text-5xl font-extrabold text-cq-text md:mb-8 xl:text-6xl"
				>
					구역 순위
				</h2>
				<ol class="zone-list">
					{#each zone_rankings as ranking, i (ranking.zone)}
						<li
							in:fly|global={{
								x: -300,
								delay: visible_zone_count * 800 - (i + 1) * 600
							}}
							class="zone-row {zone_badge_backgrounds[ranking.zone]}"
							class:is-top={i === 0}
						>
							<span class="zone-rank">{i + 1}</span>
							<span class="zone-name">{ranking.zone}</span>
							<span class="zone-score">{ranking.score}</span>
							<span class="zone-meta">{ranking.players}명</span>
						</li>
					{/each}
				</ol>
			</section>
		{/if}
		<section class="player-column">
			<h2
				in:fly|global={{ y: -120, delay: 0 }}
				class="mb-6 text-center text-5xl font-extrabold text-cq-text md:mb-8 xl:text-6xl"
			>
				개인 순위
			</h2>
			<div class="player-list">
				{#each visible_player_names as player, i (player)}
					{@const player_zone = getPlayerZone(player)}
					<p
						in:fly|global={{
							y: -300,
							delay: visible_player_count * 800 - (i + 1) * 600
						}}
						style="font-size: clamp(2.25rem, {Math.max(
							2.25,
							visible_player_count + 1.5 - i / 1.5
						)}rem, {has_zone_rankings ? 5 : 7}rem)"
						class="player-row text-center leading-tight"
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
		</section>
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
				<p class="mt-4 text-center text-2xl font-semibold text-cq-muted md:text-3xl">
					{$t('play_page.your_place', { place: current_player_place })}
				</p>
			</div>
		</div>
	{/if}
{/if}

<style>
	.results-layout {
		display: flex;
		flex-direction: column;
		gap: 2rem;
	}
	@media (min-width: 1024px) {
		.results-layout.has-zones {
			display: grid;
			grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
			gap: 3rem;
			align-items: start;
		}
	}
	@media (min-width: 1280px) {
		.results-layout.has-zones {
			gap: 4rem;
			padding-left: 3rem;
			padding-right: 3rem;
		}
	}

	.zone-list {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
		list-style: none;
		margin: 0;
		padding: 0;
	}
	@media (min-width: 1280px) {
		.zone-list {
			gap: 1rem;
		}
	}

	.zone-row {
		display: grid;
		grid-template-columns: auto 1fr auto auto;
		align-items: center;
		gap: 1rem;
		border-width: 3px;
		border-style: solid;
		border-radius: 1rem;
		padding: 0.85rem 1.25rem;
		font-weight: 700;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
	}
	@media (min-width: 1280px) {
		.zone-row {
			padding: 1.1rem 1.75rem;
			gap: 1.5rem;
		}
	}
	.zone-row.is-top {
		transform: scale(1.04);
		box-shadow: 0 8px 24px rgba(0, 0, 0, 0.18);
	}
	.zone-rank {
		font-size: 2.25rem;
		font-weight: 800;
		min-width: 2.5rem;
		text-align: center;
		font-variant-numeric: tabular-nums;
	}
	.zone-row.is-top .zone-rank {
		font-size: 3rem;
	}
	.zone-name {
		font-size: 2rem;
		font-weight: 800;
	}
	.zone-row.is-top .zone-name {
		font-size: 2.5rem;
	}
	.zone-score {
		font-size: 2.25rem;
		font-weight: 800;
		font-variant-numeric: tabular-nums;
	}
	.zone-row.is-top .zone-score {
		font-size: 2.75rem;
	}
	.zone-meta {
		font-size: 1rem;
		font-weight: 600;
		opacity: 0.7;
	}
	@media (min-width: 1280px) {
		.zone-rank {
			font-size: 2.75rem;
		}
		.zone-row.is-top .zone-rank {
			font-size: 3.75rem;
		}
		.zone-name {
			font-size: 2.5rem;
		}
		.zone-row.is-top .zone-name {
			font-size: 3rem;
		}
		.zone-score {
			font-size: 2.75rem;
		}
		.zone-row.is-top .zone-score {
			font-size: 3.5rem;
		}
		.zone-meta {
			font-size: 1.25rem;
		}
	}

	.player-list {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}
	.player-row {
		margin: 0;
	}

	.zone-badge {
		display: inline-flex;
		align-items: center;
		border-width: 2px;
		border-radius: 9999px;
		padding: 0.25rem 0.7rem;
		font-size: 0.55em;
		font-weight: 700;
		line-height: 1;
		text-transform: uppercase;
		vertical-align: middle;
	}
</style>
