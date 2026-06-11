<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import { flip } from 'svelte/animate';
	import { fade, scale } from 'svelte/transition';
	import { parseParticipantKey } from '$lib/admin';
	import { formatApiDateTime } from '$lib/datetime';
	import type { Question } from '$lib/quiz_types';

	const zones = Array.from({ length: 11 }, (_, index) => `${index + 1}구역`);

	interface PlayerAnswer {
		username: string;
		right: boolean;
		zone?: string;
	}

	interface Props {
		scores: {
			[key: string]: string | number;
		};
		title: string;
		timestamp: string;
		answers?: PlayerAnswer[][];
		questions?: Question[];
		player_zone_data?: {
			[key: string]: string;
		};
	}

	let {
		scores,
		title,
		timestamp,
		answers = [],
		questions = [],
		player_zone_data = {}
	}: Props = $props();

	const players = Object.entries(scores).map(([key, value]) => ({
		key,
		score: parseFloat(String(value)) || 0
	}));
	const player_count = players.length;
	const total_score = players.reduce((sum, p) => sum + p.score, 0);
	const average_score = player_count ? total_score / player_count : 0;

	const top_player = [...players].sort((a, b) => b.score - a.score)[0];
	const top_player_display = (() => {
		if (!top_player) return null;
		const parsed = parseParticipantKey(top_player.key);
		const zone = parsed.zone ?? player_zone_data[top_player.key];
		return zone ? `${zone}-${parsed.username}` : parsed.username;
	})();

	let total_correct = 0;
	let total_answers = 0;
	for (const q_answers of answers) {
		for (const a of q_answers) {
			total_answers += 1;
			if (a.right) total_correct += 1;
		}
	}
	const accuracy = total_answers ? (total_correct / total_answers) * 100 : 0;

	const has_zone_data = Object.keys(player_zone_data).length !== 0;
	const zone_totals = zones.map((zone) => {
		let score = 0;
		let count = 0;
		for (const [key, player_zone] of Object.entries(player_zone_data)) {
			if (player_zone !== zone) continue;
			score += parseFloat(String(scores[key] ?? 0)) || 0;
			count += 1;
		}
		return { zone, score, count };
	});
	const active_zones = zone_totals.filter((z) => z.count > 0);
	const max_zone_score = Math.max(...zone_totals.map((z) => z.score), 0);

	const zone_ranks = (() => {
		const map = new Map<string, number>();
		const ranked = [...active_zones].sort((a, b) => b.score - a.score);
		let rank = 0;
		let prev_score = Number.POSITIVE_INFINITY;
		ranked.forEach((zt, i) => {
			if (zt.score !== prev_score) {
				rank = i + 1;
				prev_score = zt.score;
			}
			map.set(zt.zone, rank);
		});
		return map;
	})();

	const date_str = formatApiDateTime(timestamp);
	const formatNumber = (n: number, digits = 0) =>
		n.toLocaleString(undefined, { maximumFractionDigits: digits });

	const zone_bar_color = (rank: number | undefined): string => {
		if (rank === 1) return 'var(--cq-brand-deep)';
		if (rank === 2) return 'var(--cq-brand)';
		if (rank === 3) return 'var(--cq-accent)';
		if (rank === undefined) return 'var(--cq-brand-mist)';
		return 'var(--cq-brand-soft)';
	};

	let zone_sort_mode = $state<'zone' | 'rank'>('zone');
	let displayed_zone_totals = $derived(
		zone_sort_mode === 'rank'
			? [...zone_totals].sort((a, b) => b.score - a.score)
			: zone_totals
	);

	let expanded = $state(false);

	const handleKey = (e: KeyboardEvent) => {
		if (e.key === 'Escape' && expanded) {
			expanded = false;
		}
	};

	$effect(() => {
		if (!expanded) return;
		const prev = document.body.style.overflow;
		document.body.style.overflow = 'hidden';
		return () => {
			document.body.style.overflow = prev;
		};
	});
</script>

<svelte:window onkeydown={handleKey} />

{#snippet sortToggle(size: 'sm' | 'lg')}
	<div
		class="flex cq-surface-muted rounded overflow-hidden border border-cq-border"
		class:text-xs={size === 'sm'}
		class:text-base={size === 'lg'}
	>
		<button
			type="button"
			class="transition-colors"
			class:px-3={size === 'sm'}
			class:py-1={size === 'sm'}
			class:px-5={size === 'lg'}
			class:py-2={size === 'lg'}
			class:bg-cq-brand={zone_sort_mode === 'zone'}
			class:text-white={zone_sort_mode === 'zone'}
			class:text-cq-muted={zone_sort_mode !== 'zone'}
			onclick={() => (zone_sort_mode = 'zone')}
		>
			구역순
		</button>
		<button
			type="button"
			class="transition-colors"
			class:px-3={size === 'sm'}
			class:py-1={size === 'sm'}
			class:px-5={size === 'lg'}
			class:py-2={size === 'lg'}
			class:bg-cq-brand={zone_sort_mode === 'rank'}
			class:text-white={zone_sort_mode === 'rank'}
			class:text-cq-muted={zone_sort_mode !== 'rank'}
			onclick={() => (zone_sort_mode = 'rank')}
		>
			등수순
		</button>
	</div>
{/snippet}

<div class="w-full flex flex-col items-center gap-4 text-cq-text">
	<div class="w-11/12 cq-card p-6 flex flex-col gap-2">
		<p class="text-xs uppercase tracking-wide text-cq-muted">{date_str}</p>
		<h1 class="text-3xl font-semibold leading-tight">{@html title}</h1>
		<div class="flex flex-wrap gap-2 mt-2 text-xs">
			<span class="cq-surface-muted px-2 py-1 rounded">{questions.length}문제</span>
			{#if has_zone_data}
				<span class="cq-surface-muted px-2 py-1 rounded">{active_zones.length}개 구역</span>
			{/if}
		</div>
	</div>

	<div class="w-11/12 grid grid-cols-2 md:grid-cols-4 gap-3">
		<div class="cq-card p-4 flex flex-col gap-1">
			<p class="text-xs text-cq-muted">참가자</p>
			<p class="text-2xl font-semibold">{player_count}</p>
		</div>
		<div class="cq-card p-4 flex flex-col gap-1">
			<p class="text-xs text-cq-muted">평균 점수</p>
			<p class="text-2xl font-semibold">{formatNumber(average_score, 1)}</p>
		</div>
		<div class="cq-card p-4 flex flex-col gap-1">
			<p class="text-xs text-cq-muted">최고 점수</p>
			<p class="text-2xl font-semibold">
				{top_player ? formatNumber(top_player.score) : '-'}
			</p>
			{#if top_player_display}
				<p class="text-xs text-cq-muted truncate">{top_player_display}</p>
			{/if}
		</div>
		<div class="cq-card p-4 flex flex-col gap-1">
			<p class="text-xs text-cq-muted">정답률</p>
			<p class="text-2xl font-semibold">{formatNumber(accuracy, 1)}%</p>
			<p class="text-xs text-cq-muted">{total_correct} / {total_answers}</p>
		</div>
	</div>

	{#if has_zone_data}
		<div class="w-11/12 cq-card p-4">
			<div class="flex items-center justify-between mb-3 gap-2">
				<p class="text-sm font-semibold">구역별 합계</p>
				<div class="flex items-center gap-2">
					{@render sortToggle('sm')}
					<button
						type="button"
						class="cq-surface-muted w-8 h-8 rounded border border-cq-border text-cq-muted hover:bg-cq-brand hover:text-white transition-colors flex items-center justify-center"
						onclick={() => (expanded = true)}
						aria-label="크게 보기"
						title="크게 보기"
					>
						<svg
							xmlns="http://www.w3.org/2000/svg"
							viewBox="0 0 24 24"
							fill="none"
							stroke="currentColor"
							stroke-width="2"
							stroke-linecap="round"
							stroke-linejoin="round"
							class="w-4 h-4"
						>
							<path d="M15 3h6v6" />
							<path d="M9 21H3v-6" />
							<path d="M21 3l-7 7" />
							<path d="M3 21l7-7" />
						</svg>
					</button>
				</div>
			</div>
			<div class="flex flex-col gap-2">
				{#each displayed_zone_totals as zt (zt.zone)}
					{@const rank = zone_ranks.get(zt.zone)}
					<div
						animate:flip={{ duration: 350 }}
						class="flex items-center gap-3"
					>
						<span
							class="w-6 text-center text-sm tabular-nums shrink-0"
							class:font-bold={rank === 1}
							class:text-cq-brand={rank === 1}
							class:font-semibold={rank !== undefined && rank !== 1}
							class:text-cq-muted={rank === undefined}
						>
							{rank ?? '-'}
						</span>
						<span class="w-12 text-xs text-cq-muted shrink-0">{zt.zone}</span>
						<div class="flex-1 h-2 cq-surface-muted rounded overflow-hidden">
							<span
								class="block h-full transition-all duration-300"
								style="width: {max_zone_score
									? (zt.score / max_zone_score) * 100
									: 0}%; background: {zone_bar_color(rank)};"
							></span>
						</div>
						<span class="w-20 text-right text-sm tabular-nums"
							>{formatNumber(zt.score)}</span
						>
						<span class="w-10 text-right text-xs text-cq-muted">{zt.count}명</span>
					</div>
				{/each}
			</div>
		</div>
	{/if}
</div>

{#if expanded}
	<div
		class="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex p-4 sm:p-8"
		transition:fade={{ duration: 150 }}
		onclick={(e) => {
			if (e.target === e.currentTarget) expanded = false;
		}}
		onkeydown={(e) => {
			if (e.key === 'Escape') expanded = false;
		}}
		role="dialog"
		aria-modal="true"
		tabindex="-1"
	>
		<div
			class="cq-card flex flex-col p-6 sm:p-10 m-auto max-w-7xl w-full max-h-full overflow-auto"
			transition:scale={{ duration: 180, start: 0.96 }}
		>
			<div class="flex items-center justify-between mb-8 gap-4 flex-wrap">
				<h2 class="text-3xl sm:text-4xl font-bold">구역별 합계</h2>
				<div class="flex items-center gap-3">
					{@render sortToggle('lg')}
					<button
						type="button"
						class="cq-surface-muted w-10 h-10 sm:w-12 sm:h-12 rounded border border-cq-border text-cq-muted hover:bg-cq-accent hover:text-white transition-colors flex items-center justify-center"
						onclick={() => (expanded = false)}
						aria-label="닫기"
						title="닫기 (ESC)"
					>
						<svg
							xmlns="http://www.w3.org/2000/svg"
							viewBox="0 0 24 24"
							fill="none"
							stroke="currentColor"
							stroke-width="2"
							stroke-linecap="round"
							stroke-linejoin="round"
							class="w-5 h-5"
						>
							<path d="M18 6L6 18" />
							<path d="M6 6l12 12" />
						</svg>
					</button>
				</div>
			</div>
			<div class="flex flex-col gap-4 sm:gap-5">
				{#each displayed_zone_totals as zt (zt.zone)}
					{@const rank = zone_ranks.get(zt.zone)}
					<div
						animate:flip={{ duration: 350 }}
						class="flex items-center gap-6"
					>
						<span
							class="w-16 text-center text-5xl tabular-nums shrink-0"
							class:font-bold={rank === 1}
							class:text-cq-brand={rank === 1}
							class:font-semibold={rank !== undefined && rank !== 1}
							class:text-cq-muted={rank === undefined}
						>
							{rank ?? '-'}
						</span>
						<span class="w-28 text-2xl text-cq-muted shrink-0">{zt.zone}</span>
						<div class="flex-1 h-8 cq-surface-muted rounded overflow-hidden">
							<span
								class="block h-full transition-all duration-300"
								style="width: {max_zone_score
									? (zt.score / max_zone_score) * 100
									: 0}%; background: {zone_bar_color(rank)};"
							></span>
						</div>
						<span class="w-40 text-right text-4xl tabular-nums font-semibold shrink-0">
							{formatNumber(zt.score)}
						</span>
						<span class="w-20 text-right text-xl text-cq-muted shrink-0">
							{zt.count}명
						</span>
					</div>
				{/each}
			</div>
		</div>
	</div>
{/if}
