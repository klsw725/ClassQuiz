<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import type { QuizData } from '$lib/quiz_types';
	import { onMount } from 'svelte';
	import { fade } from 'svelte/transition';
	import { getLocalization } from '$lib/i18n';

	const { t } = getLocalization();

	export let quiz: QuizData | undefined = undefined;

	const on_parent_click = (e: Event) => {
		if (e.target !== e.currentTarget) {
			return;
		}
		quiz = undefined;
	};
	const close_start_game_if_esc_is_pressed = (key: KeyboardEvent) => {
		if (key.code === 'Escape') {
			quiz = undefined;
		}
	};
	onMount(() => {
		document.body.addEventListener('keydown', close_start_game_if_esc_is_pressed);
	});
</script>

{#if quiz}
	<div
		class="fixed w-full h-full top-0 flex bg-black/50 z-50 overflow-scroll"
		onclick={on_parent_click}
		transition:fade={{ duration: 100 }}
	>
		<div
			class="cq-card m-auto flex p-4 flex-col lg:w-2/3 w-11/12 h-5/6"
		>
			<h1 class="text-center text-5xl text-cq-text">{$t('words.analytics')}</h1>
			<section class="flex flex-col gap-2 mt-8">
				<h2 class="mx-auto text-2xl text-cq-text">{$t('words.rating')}</h2>
				<table class="cq-surface w-fit mx-auto">
					<tbody>
						<tr class="border-b-2 text-left border-cq-border">
							<th class="border-r p-1 mx-auto border-cq-border"
								>{$t('words.like', { count: 2 })}</th
							>
							<th class="p-1 mx-auto">{$t('words.dislike', { count: 2 })}</th>
						</tr>
						<tr class="text-left">
							<td class="border-r p-1 border-cq-border"
								>{quiz.likes}</td
							>
							<td class="mx-auto p-1">{quiz.dislikes}</td>
						</tr>
					</tbody>
				</table>
			</section>
			<section class="flex flex-col gap-2 mt-8">
				<h2 class="mx-auto text-2xl text-cq-text">{$t('dashboard.views_n_plays')}</h2>
				<table class="cq-surface w-fit mx-auto">
					<thead>
						<tr class="border-b-2 text-left border-cq-border">
							<th class="border-r p-1 mx-auto border-cq-border"
								>{$t('words.view', { count: 2 })}</th
							>
							<th class="p-1 mx-auto">{$t('words.play', { count: 2 })}</th>
						</tr>
					</thead>
					<tbody>
						<tr class="text-left">
							<td class="border-r p-1 border-cq-border"
								>{quiz.views}</td
							>
							<td class="mx-auto p-1">{quiz.plays}</td>
						</tr>
					</tbody>
				</table>
			</section>
			<section class="flex flex-col gap-2 mt-8">
				<h2 class="mx-auto text-2xl text-cq-text">{$t('words.info')}</h2>
				<p class="mx-auto max-w-[70%] text-center text-cq-muted">
					{$t('dashboard.info_analytics')}
				</p>
			</section>
			<section class="mt-auto">
				<p class="mt-6 mx-auto max-w-[70%] text-sm text-cq-muted text-center">
					Since there's still some space left down here, I guess that I take this
					opportunity to thank You for using ClassQuiz! Have a great day and continue
					using ClassQuiz ;)
				</p>
			</section>
		</div>
	</div>
{/if}
