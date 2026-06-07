<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import VotingResults from './voting_results.svelte';
	import { flip } from 'svelte/animate';
	import { fly } from 'svelte/transition';
	import { onMount } from 'svelte';
	import { getLocalization } from '$lib/i18n';
	import { parseParticipantKey, participantKey } from '$lib/admin';
	import type { Question } from '$lib/quiz_types';
	import { QuizQuestionType } from '$lib/quiz_types';

	const { t } = getLocalization();
	const LIVE_SCORE_VISIBLE_PLAYER_LIMIT = 6;

	type ZoneNumber = 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11;
	type SupportedZone = `${ZoneNumber}구역`;
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
	const zone_badge_fallback = 'border-cq-border bg-cq-surface-muted text-cq-text';
	const getZoneBadgeClasses = (zone: string) =>
		(zone_badge_backgrounds as Record<string, string>)[zone] ?? zone_badge_fallback;

	interface AnswerDetail {
		answer: string;
		matched: boolean;
	}

	interface Props {
		data: any;
		question: Question;
		new_data: Array<{
			username: string;
			answer: string;
			answer_details?: AnswerDetail[];
			right: boolean;
			time_taken: number;
			score: number;
			zone?: string;
		}>;
		player_display_names?: Record<string, string>;
	}

	let { data = $bindable(), question, new_data, player_display_names = {} }: Props = $props();

	// let data_by_username = {};

	const group_username_by_score = (_new_d: any[]): object => {
		let ret_data = {};
		for (const i of new_data) {
			ret_data[participantKey(i.username, i.zone)] = i.score;
		}
		return ret_data;
	};
	let score_by_username = $derived(group_username_by_score(new_data));
	let answer_display_names = $derived(
		Object.fromEntries(
			new_data
				.filter((answer) => answer.zone)
				.map((answer) => [
					participantKey(answer.username, answer.zone),
					`${answer.zone}-${answer.username}`
				])
		)
	);
	const formatPlayerName = (username: string) =>
		answer_display_names[username] ??
		player_display_names[username] ??
		parseParticipantKey(username).username;

	let player_names = $derived(
		Object.keys(data).sort((a, b) => {
			const scoreA = parseFloat(data[a]) || 0;
			const scoreB = parseFloat(data[b]) || 0;
			return scoreB - scoreA;
		})
	);
	let visible_player_names = $derived(player_names.slice(0, LIVE_SCORE_VISIBLE_PLAYER_LIMIT));

	let zones = $derived.by(() => {
		const seen = new Set<string>();
		for (const key of Object.keys(data)) {
			const { zone } = parseParticipantKey(key);
			if (zone) seen.add(zone);
		}
		for (const entry of new_data) {
			if (entry.zone) seen.add(entry.zone);
		}
		return [...seen].sort((a, b) => (parseInt(a, 10) || 0) - (parseInt(b, 10) || 0));
	});

	let zone_totals = $derived.by(() => {
		const totals: Record<string, { score: number; players: number }> = {};
		for (const zone of zones) {
			totals[zone] = { score: 0, players: 0 };
		}
		for (const key of Object.keys(data)) {
			const { zone } = parseParticipantKey(key);
			if (!zone || !totals[zone]) continue;
			totals[zone].score += parseFloat(data[key]) || 0;
			totals[zone].players += 1;
		}
		return totals;
	});

	let selected_zones = $state(new Set<string>());

	const toggleZone = (zone: string) => {
		const next = new Set(selected_zones);
		if (next.has(zone)) next.delete(zone);
		else next.add(zone);
		selected_zones = next;
	};

	let selected_total = $derived(
		[...selected_zones].reduce((sum, zone) => sum + (zone_totals[zone]?.score ?? 0), 0)
	);
	let selected_player_count = $derived(
		[...selected_zones].reduce((sum, zone) => sum + (zone_totals[zone]?.players ?? 0), 0)
	);

	if (JSON.stringify(data) === '{}') {
		for (const i of new_data) {
			data[participantKey(i.username, i.zone)] = 0;
		}
	}

	let show_new_score_clicked = $state(false);

	const show_new_score = () => {
		for (const i of player_names) {
			if (isNaN(data[i])) {
				data[i] = 0;
			}
			console.log(score_by_username[i], '1');
			data[i] = (score_by_username[i] ?? 0) + data[i];
		}
		for (const i of new_data) {
			const key = participantKey(i.username, i.zone);
			if (!data[key]) {
				data[key] = score_by_username[key];
			}
		}
		show_new_score_clicked = true;
		setTimeout(() => {
			data = { ...data };
		}, 800);
	};

	onMount(() => {
		setTimeout(show_new_score, 1000);
	});

	// https://svelte.dev/repl/96a58afdea2248a5b7e489160ffba887?version=3.44.2
</script>

<div class="h-full flex flex-col">
	<div class="flex justify-center overflow-x-auto px-2 py-2 md:py-4">
		<div class="cq-card mx-auto min-w-fit overflow-hidden p-2 md:p-3">
			<table class="mx-auto table-auto text-2xl md:text-3xl lg:text-4xl">
				<thead class="cq-surface-muted">
					<tr>
						<th
							class="p-3 md:p-5 border-r border-cq-border border-b-2 border-b-cq-border"
							>{$t('words.name')}</th
						>
						<th class="p-3 md:p-5 border-b-2 border-b-cq-border"
							>{$t('words.point', { count: 2 })}</th
						>
						{#if show_new_score_clicked}
							<th
								in:fly|global={{ x: 300 }}
								class="p-3 md:p-5 border-b-2 border-b-cq-border"
								>{$t('play_page.points_added')}
							</th>
						{/if}
					</tr>
				</thead>
				<tbody class="divide-y divide-cq-border text-cq-text">
					{#each visible_player_names as player (player)}
						<tr animate:flip class="odd:bg-cq-surface even:bg-cq-surface-muted">
							<td class="p-3 md:p-5 border-r border-cq-border font-semibold"
								>{formatPlayerName(player)}</td
							>
							<td class="p-3 md:p-5 font-bold text-cq-brand">{data[player]}</td>
							{#if show_new_score_clicked}
								<td
									in:fly|global={{ x: 300 }}
									class="p-3 md:p-5 font-bold text-cq-brand"
									class:text-red-600={score_by_username[player] === 0 ||
										score_by_username[player] === undefined}
								>
									+{score_by_username[player] ?? '0'}
								</td>
							{/if}
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	</div>
	{#if zones.length}
		<div class="flex justify-center px-2 mt-6 md:mt-8">
			<div class="cq-card w-full max-w-3xl p-4 md:p-6">
				<div class="flex flex-wrap items-center justify-between gap-2">
					<p class="text-cq-muted text-base font-semibold md:text-lg">구역 합산</p>
					{#if selected_zones.size > 0}
						<button
							type="button"
							class="text-cq-muted hover:text-cq-text text-sm underline"
							onclick={() => (selected_zones = new Set())}
						>
							선택 해제
						</button>
					{/if}
				</div>
				<div class="mt-3 flex flex-wrap justify-center gap-2">
					{#each zones as zone (zone)}
						{@const total = zone_totals[zone]?.score ?? 0}
						{@const is_selected = selected_zones.has(zone)}
						<button
							type="button"
							onclick={() => toggleZone(zone)}
							class="zone-chip {getZoneBadgeClasses(zone)}"
							class:is-selected={is_selected}
						>
							<span class="chip-check" aria-hidden="true">{is_selected ? '✓' : ''}</span>
							<span class="font-bold">{zone}</span>
							<span class="chip-score">{total}</span>
						</button>
					{/each}
				</div>
				<div class="cq-surface-muted mt-4 rounded-lg border-2 border-cq-border p-3 text-center md:p-4">
					{#if selected_zones.size === 0}
						<p class="text-cq-muted text-lg md:text-xl">
							구역을 선택하면 합산 점수가 표시됩니다
						</p>
					{:else}
						<p class="text-cq-muted text-sm md:text-base">
							선택 {selected_zones.size}구역 · 참여자 {selected_player_count}명
						</p>
						<p class="text-cq-brand mt-1 text-3xl font-bold md:text-4xl">
							{selected_total}
						</p>
					{/if}
				</div>
			</div>
		</div>
	{/if}
	{#if [QuizQuestionType.ABCD, QuizQuestionType.VOTING, QuizQuestionType.TEXT, QuizQuestionType.MULTI_TEXT].includes(question.type)}
		<div class="mt-14 md:mt-20">
			<VotingResults data={new_data} {question} />
		</div>
	{/if}
</div>

<style>
	.zone-chip {
		display: inline-flex;
		align-items: center;
		gap: 0.5rem;
		border-width: 2px;
		border-radius: 9999px;
		padding: 0.4rem 0.9rem;
		font-size: 1rem;
		line-height: 1;
		transition: transform 0.15s ease, box-shadow 0.15s ease, opacity 0.15s ease;
		opacity: 0.7;
	}
	.zone-chip:hover {
		transform: translateY(-1px);
	}
	.zone-chip.is-selected {
		opacity: 1;
		box-shadow: 0 0 0 3px var(--cq-brand, currentColor);
	}
	.chip-check {
		display: inline-flex;
		justify-content: center;
		align-items: center;
		width: 1rem;
		font-weight: 700;
	}
	.chip-score {
		font-variant-numeric: tabular-nums;
		font-weight: 700;
		opacity: 0.85;
	}
</style>
