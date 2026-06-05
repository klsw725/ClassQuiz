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
	const LIVE_SCORE_VISIBLE_PLAYER_LIMIT = 4;

	interface Props {
		data: any;
		question: Question;
		new_data: Array<{
			username: string;
			answer: string;
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
	{#if [QuizQuestionType.ABCD, QuizQuestionType.VOTING].includes(question.type)}
		<div class="mt-14 md:mt-20">
			<VotingResults data={new_data} {question} />
		</div>
	{/if}
</div>
