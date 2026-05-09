<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import { getLocalization } from '$lib/i18n';

	const { t } = getLocalization();
	interface Props {
		scores: {
			[key: string]: string;
		};
		custom_field: {
			[key: string]: string;
		};
		answers: { [key: string]: any }[];
	}

	let { scores, custom_field, answers }: Props = $props();

	let usernames = $derived(
        Object.keys(scores).sort((a, b) => {
            const scoreA = parseFloat(scores[a]) || 0;
            const scoreB = parseFloat(scores[b]) || 0;
            return scoreB - scoreA;
        })
    );

	const correctCounts = {};
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
	<div class="flex justify-center w-full">
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
				{#each usernames as uname}
					<tr class="text-left">
					<td class="border-r p-1 border-cq-border">{uname}</td>
					<td class="border-r p-1 border-cq-border"
						>{correctCounts[uname]}</td
					>
						<td class="p-1">{scores[uname]}</td>
						{#if custom_field[uname]}
						<td class="border-l p-1 border-cq-border"
								>{custom_field[uname]}</td
							>
						{/if}
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
</div>
