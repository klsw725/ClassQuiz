<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import type { PageData } from './$types';
	import BrownButton from '$lib/components/buttons/brown.svelte';
	import { getLocalization } from '$lib/i18n';
	const { t } = getLocalization();
	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	const controllers: [] = data.controllers;
</script>

<div class="min-h-screen w-full p-4 text-cq-text">
	{#if controllers.length === 0}
		<div class="flex min-h-[50vh] w-full items-center justify-center">
			<div class="cq-card flex flex-col items-center gap-4 p-8 text-center">
				<BrownButton href="/account/controllers/add"
					>{$t('controllers.add_new_controller')}</BrownButton
				>
			</div>
		</div>
	{:else}
		<div class="cq-card overflow-hidden p-4">
			<div class="flex pb-4">
				<div class="mx-auto">
					<BrownButton href="/account/controllers/add"
						>{$t('controllers.add_new_controller')}</BrownButton
					>
				</div>
			</div>
			<div class="overflow-x-auto">
				<table class="w-full">
					<thead>
						<tr class="border-b border-cq-border text-left text-cq-muted">
							<th class="border-r border-cq-border p-2 mx-auto">{$t('words.name')}</th
							>
							<th class="border-r border-cq-border p-2 mx-auto"
								>{$t('controllers.player_name')}
							</th>
							<th class="border-r border-cq-border p-2 mx-auto"
								>{$t('controllers.first_seen')}
							</th>
							<th class="border-r border-cq-border p-2 mx-auto"
								>{$t('controllers.last_seen')}
							</th>
							<th class="mx-auto p-2">{$t('words.version')}</th>
						</tr>
					</thead>
					<tbody>
						{#each data.controllers as controller}
							<tr class="border-b border-cq-border text-left last:border-b-0">
								<td class="border-r border-cq-border p-2"
									><a
										href="/account/controllers/{controller.id}"
										class="link-hover text-lg font-semibold text-cq-text underline decoration-cq-border underline-offset-4"
										>{controller.name}</a
									></td
								>
								<td class="border-r border-cq-border p-2 text-cq-muted"
									>{controller.player_name}</td
								>
								<td class="border-r border-cq-border p-2 text-cq-muted"
									>{controller.first_seen
										? new Date(controller.first_seen).toLocaleString()
										: $t('words.never')}</td
								>
								<td class="border-r border-cq-border p-2 text-cq-muted"
									>{controller.last_seen
										? new Date(controller.last_seen).toLocaleString()
										: $t('words.never')}</td
								>
								<td class="mx-auto p-2 text-cq-muted"
									>{controller.os_version ?? $t('words.unknown')}</td
								>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</div>
	{/if}
</div>
