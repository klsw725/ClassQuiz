<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import { getLocalization } from '$lib/i18n';

	const { t } = getLocalization();
	const zones = Array.from({ length: 11 }, (_, index) => `${index + 1}구역`);
	const RESULT_TABLE_PAGE_SIZE = 100;

	interface PlayerAnswer {
		username: string;
		right: boolean;
	}

	interface Props {
		scores: {
			[key: string]: string | number;
		};
		custom_field: {
			[key: string]: string;
		};
		player_zone_data: {
			[key: string]: string;
		};
		answers: PlayerAnswer[][];
	}

	let { scores, custom_field, player_zone_data, answers }: Props = $props();

	let usernames = $derived(
		Object.keys(scores).sort((a, b) => {
			const scoreA = parseFloat(String(scores[a])) || 0;
			const scoreB = parseFloat(String(scores[b])) || 0;
			return scoreB - scoreA;
		})
	);
	let visible_player_count = $state(RESULT_TABLE_PAGE_SIZE);
	let visible_usernames = $derived(usernames.slice(0, visible_player_count));
	let hidden_player_count = $derived(
		Math.max(usernames.length - visible_usernames.length, 0)
	);
	let has_zone_data = $derived(Object.keys(player_zone_data).length !== 0);
	let zone_totals = $derived(
		zones.map((zone) => ({
			zone,
			score: Object.entries(player_zone_data).reduce((total, [username, player_zone]) => {
				if (player_zone !== zone) {
					return total;
				}
				return total + (parseFloat(String(scores[username] ?? 0)) || 0);
			}, 0)
		}))
	);

	const correctCounts: Record<string, number> = {};
	answers.forEach((questionAnswers) => {
		questionAnswers.forEach((answer) => {
			const user = answer.username;
			if (!correctCounts[user]) {
				correctCounts[user] = 0;
			}
			if (answer.right) {
				correctCounts[user] += 1;
			}
		});
	});
</script>

<div class="w-full text-cq-text">
	<div class="flex w-full flex-col items-center gap-4">
		{#if has_zone_data}
			<table class="cq-surface w-11/12 m-auto">
				<thead>
					<tr class="border-b-2 text-left border-cq-border">
						<th class="border-r p-1 mx-auto border-cq-border">구역</th>
						<th class="p-1 mx-auto">{$t('result_page.player_score')}</th>
					</tr>
				</thead>
				<tbody>
					{#each zone_totals as zone_total (zone_total.zone)}
						<tr class="text-left">
							<td class="border-r p-1 border-cq-border">{zone_total.zone}</td>
							<td class="p-1">{zone_total.score}</td>
						</tr>
					{/each}
				</tbody>
			</table>
		{/if}
		<div class="w-11/12 text-sm font-semibold text-cq-muted">
			{visible_usernames.length}/{usernames.length}
		</div>
		<table class="cq-surface w-11/12 m-auto">
			<thead>
				<tr class="border-b-2 text-left border-cq-border">
					<th class="border-r p-1 mx-auto border-cq-border"
						>{$t('result_page.player_name')}
					</th>
					<th class="border-r p-1 mx-auto border-cq-border"
						>{$t('result_page.player_correct_questions')}
					</th>
					<th class="p-1 mx-auto">{$t('result_page.player_score')}</th>
					{#if Object.keys(custom_field).length !== 0}
						<th class="border-l p-1 mx-auto border-cq-border"
							>{$t('result_page.custom_field')}
						</th>
					{/if}
				</tr>
			</thead>
			<tbody>
				{#each visible_usernames as uname (uname)}
					<tr class="text-left">
						<td class="border-r p-1 border-cq-border">{uname}</td>
						<td class="border-r p-1 border-cq-border">{correctCounts[uname]}</td>
						<td class="p-1">{scores[uname]}</td>
						{#if custom_field[uname]}
							<td class="border-l p-1 border-cq-border">{custom_field[uname]}</td>
						{/if}
					</tr>
				{/each}
			</tbody>
		</table>
		{#if hidden_player_count > 0}
			<button
				type="button"
				class="cq-surface-muted w-11/12 m-auto p-2 font-semibold text-cq-muted hover:text-cq-text transition"
				onclick={() => (visible_player_count += RESULT_TABLE_PAGE_SIZE)}
			>
				+{Math.min(RESULT_TABLE_PAGE_SIZE, hidden_player_count)}
			</button>
		{/if}
	</div>
</div>
