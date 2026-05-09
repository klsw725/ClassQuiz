<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import type { PageData } from './$types';
	import { getLocalization } from '$lib/i18n';

	const { t } = getLocalization();

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();
</script>

<div class="w-full text-cq-text">
	<div class="flex justify-center w-full">
		<div class="w-11/12 m-auto">
			{#if data.results.length === 0}
				<p class="text-center text-3xl mt-8 text-cq-muted">{$t('results_page.no_results_so_far')}</p>
			{:else}
				<table class="cq-surface w-full">
					<thead>
						<tr class="border-b-2 text-left border-cq-border">
							<th class="border-r p-1 mx-auto border-cq-border"
								>{$t('results_page.quiz_title')}
							</th>
							<th class="border-r p-1 mx-auto border-cq-border"
								>{$t('results_page.date_played')}
							</th>
							<th class="border-r p-1 mx-auto border-cq-border"
								>{$t('results_page.player_count')}
							</th>
							<th class="mx-auto p-1">{$t('words.note')}</th>
						</tr>
					</thead>
					<tbody>
						{#each data.results as result}
							<tr class="text-left">
								<td class="border-r p-1 border-cq-border"
									><a href="/results/{result.id}" class="link-hover underline text-lg"
										>{@html result.title}</a
									></td
								>
								<td class="border-r p-1 border-cq-border"
									>{new Date(result.timestamp).toLocaleString()}</td
								>
								<td class="border-r p-1 border-cq-border"
									>{Object.keys(result.player_scores).length}</td
								>
								<td class:p-1={result.note}>
									{#if result.note}
										{result.note}
									{/if}
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			{/if}
		</div>
	</div>
</div>
