<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import { getLocalization } from '$lib/i18n';

	const { t } = getLocalization();

	function sortObjectbyValue(obj) {
		const ret = {};
		Object.keys(obj)
			.sort((a, b) => obj[b] - obj[a])
			.forEach((s) => (ret[s] = obj[s]));
		return ret;
	}

	interface Props {
		scores: any;
		question_results: Array<{
			username: string;
			answer: string;
			right: boolean;
			time_taken: number;
			score: number;
		}>;
		username: any;
	}

	let { scores = $bindable(), question_results, username }: Props = $props();
	let score_by_username = $state({});
	let currentPlayerResult = $derived(
		question_results.find((result) => result.username === username)
	);

	if (JSON.stringify(scores) === '{}') {
		for (const i of question_results) {
			scores[i.username] = 0;
		}
	}
	for (const i of question_results) {
		score_by_username[i.username] = i.score;
	}
	for (const username of Object.keys(score_by_username)) {
		scores[username] = (score_by_username[username] ?? 0) + (scores[username] ?? 0);
	}
	scores = scores;
	let sorted_scores = $derived(sortObjectbyValue(scores));
</script>

<div class="flex min-h-screen items-center justify-center px-4 text-cq-text">
	<div
		class="cq-card flex w-full max-w-md flex-col gap-7 p-8 text-center shadow-2xl md:max-w-xl md:p-10"
	>
		<p
			class="cq-surface-muted rounded-lg border-2 border-cq-border p-6 text-5xl font-bold text-cq-brand md:p-8 md:text-7xl"
		>
			+{score_by_username[username] ?? '0'}
		</p>
		<p class="cq-surface rounded-lg px-5 py-4 text-xl font-semibold text-cq-muted md:text-2xl">
			{$t('play_page.your_score', { score: sorted_scores[username] ?? '0' })}
		</p>
		{#if currentPlayerResult}
			<p
				class="cq-surface-muted rounded-lg border-2 border-cq-border px-5 py-4 text-lg font-semibold md:text-xl"
				class:text-cq-brand={currentPlayerResult.right}
				class:text-cq-accent={!currentPlayerResult.right}
			>
				{currentPlayerResult.right
					? $t('play_page.latest_question_correct')
					: $t('play_page.latest_question_incorrect')}
			</p>
		{/if}
	</div>
</div>
