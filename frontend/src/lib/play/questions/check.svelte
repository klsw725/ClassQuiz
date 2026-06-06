<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import type { Answer, Question } from '$lib/quiz_types';
	import { get_foreground_color } from '$lib/helpers';
	import { getLocalization } from '$lib/i18n';
	import { kahoot_icons } from '$lib/play/kahoot_mode_assets/kahoot_icons';
	import CircularTimer from '$lib/play/circular_progress.svelte';
	// import CircularTimer from '$lib/play/circular_progress.svelte';
	const { t } = getLocalization();
	const default_colors = ['#D6EDC9', '#B07156', '#7F7057', '#4E6E58'];

	interface Props {
		question: Question;
		selected_answer?: string;
		game_mode: any;
		timer_res: any;
		circular_progress: any;
	}

	let {
		question,
		selected_answer = $bindable(),
		game_mode,
		timer_res,
		circular_progress
	}: Props = $props();
	let answers = question.answers as Answer[];
	let _selected_answers = $state([false, false, false, false]);

	const selectAnswer = (i: number) => {
		_selected_answers[i] = !_selected_answers[i];
		selected_answer = '';
		for (let i = 0; i < _selected_answers.length; i++) {
			if (_selected_answers[i]) {
				selected_answer += String(i);
			}
		}
		console.log(_selected_answers, selected_answer);
	};
</script>

<div
	class="w-full h-[95%]"
	class:normal-mobile-check-answer={game_mode === 'normal'}
	class:normal-mobile-check-answer-available={game_mode === 'normal' && !question.image}
>
	<!--
        <div
            class="cq-surface absolute top-0 bottom-0 left-0 right-0 m-auto h-fit w-fit rounded-full border-2 border-cq-border shadow-2xl z-50"
        >
            <CircularTimer
                bind:text={timer_res}
                bind:progress={circular_prgoress}
                color="#ef4444"
            />
        </div>
    -->
	<div
		class="cq-surface absolute top-0 bottom-0 left-0 right-0 m-auto h-fit w-fit rounded-full border-2 border-cq-border shadow-2xl z-40"
		class:normal-mobile-answer-timer={game_mode === 'normal'}
	>
		<CircularTimer text={timer_res} progress={circular_progress} color="#ef4444" />
	</div>

	<div
		class="grid grid-rows-2 grid-flow-col auto-cols-auto gap-2 w-full p-4 h-full"
		class:normal-mobile-answer-grid={game_mode === 'normal'}
		class:normal-mobile-answer-grid-compact={game_mode === 'normal' && !question.image}
	>
		{#each answers as answer, i}
			<button
				class="rounded-lg h-full flex min-w-0 overflow-hidden align-middle justify-center disabled:opacity-60 p-3 border-2 border-cq-border transition-all"
				class:normal-mobile-answer-button={game_mode === 'normal'}
				style="background-color: {answer.color ??
					default_colors[i]}; color: {get_foreground_color(
					answer.color ?? default_colors[i]
				)}"
				onclick={() => selectAnswer(i)}
				class:opacity-100={_selected_answers[i]}
				class:opacity-50={!_selected_answers[i]}
			>
				{#if game_mode === 'kahoot'}
					{#if answer.emoji}
						<span
							class="m-auto text-6xl leading-none"
							aria-label={$t('admin_page.answer_emoji')}>{answer.emoji}</span
						>
					{:else}
						<img
							class="h-2/3 inline-block m-auto"
							alt={$t('admin_page.answer_icon')}
							src={kahoot_icons[i]}
						/>
					{/if}
				{:else if game_mode === 'normal'}
					<div
						class="normal-mobile-answer-content m-auto flex min-w-0 max-w-full items-center justify-center gap-3"
					>
						{#if answer.emoji}
							<span
								class="normal-mobile-answer-emoji text-4xl leading-none"
								aria-label={$t('admin_page.answer_emoji')}>{answer.emoji}</span
							>
						{:else if kahoot_icons[i]}
							<img
								class="normal-mobile-answer-icon h-12"
								alt={$t('admin_page.answer_icon')}
								src={kahoot_icons[i]}
							/>
						{/if}
						<p class="normal-mobile-answer-text min-w-0 notranslate" translate="no">
							{answer.answer}
						</p>
					</div>
				{:else}
					<p class="m-auto notranslate" translate="no">{answer.answer}</p>
				{/if}
			</button>
		{/each}
	</div>
</div>

<style>
	@media (max-width: 639px) {
		.normal-mobile-check-answer {
			height: 65svh;
			min-height: 0;
			position: relative;
		}

		.normal-mobile-check-answer-available {
			flex: 1 1 0;
			height: auto;
			max-height: 66.667svh;
			min-height: 0;
			overflow: hidden;
		}

		.normal-mobile-answer-timer {
			top: 0.5rem;
			right: auto;
			bottom: auto;
			left: 50%;
			margin: 0;
			transform: translateX(-50%) scale(0.55);
			transform-origin: top center;
		}

		.normal-mobile-answer-grid {
			grid-template-rows: minmax(0, 1fr) minmax(0, 1fr);
			gap: 0.5rem;
			height: 100%;
			padding: 5rem 0.5rem 0.5rem;
		}

		.normal-mobile-answer-grid-compact {
			padding-top: 3.5rem;
		}

		.normal-mobile-answer-button {
			padding: 0.5rem;
		}

		.normal-mobile-answer-content {
			flex-direction: column;
			gap: 0.25rem;
			text-align: center;
		}

		.normal-mobile-answer-emoji {
			font-size: 1.5rem;
		}

		.normal-mobile-answer-icon {
			height: 1.75rem;
		}

		.normal-mobile-answer-text {
			display: -webkit-box;
			line-clamp: 3;
			-webkit-box-orient: vertical;
			-webkit-line-clamp: 3;
			overflow: hidden;
			overflow-wrap: anywhere;
			font-size: clamp(0.7rem, 3vw, 0.875rem);
			line-height: 1.2;
		}
	}
</style>
