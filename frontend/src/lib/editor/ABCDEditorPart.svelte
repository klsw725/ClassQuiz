<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import { run, preventDefault } from 'svelte/legacy';

	import type { Answer, EditorData } from '../quiz_types';
	import { QuizQuestionType } from '../quiz_types';
	import { fade } from 'svelte/transition';
	import { reach } from 'yup';
	import { ABCDQuestionSchema } from '$lib/yupSchemas';
	import { getLocalization } from '$lib/i18n';
	import { get_foreground_color } from '$lib/helpers';

	const { t } = getLocalization();

	const default_colors = ['#e0413a', '#1a73c2', '#e8a020', '#2a9d54'];
	const answer_emojis = [
		'😀',
		'😄',
		'😂',
		'😍',
		'😎',
		'😮',
		'🤔',
		'🥳',
		'🙌',
		'👀',
		'💡',
		'💭',
		'⭐',
		'✨',
		'🔥',
		'💯',
		'🎯',
		'❓',
		'❗',
		'⭕',
		'🚀',
		'🌈',
		'✅',
		'❌',
		'⚡',
		'🧠',
		'📚',
		'📖',
		'✏️',
		'📝',
		'🔬',
		'🧮',
		'🌍',
		'🧩',
		'🎨',
		'🔑',
		'🛠️',
		'⏰',
		'📌',
		'💎',
		'🎲',
		'🐝',
		'🐶',
		'🐱',
		'🦊',
		'🐢',
		'🦉',
		'🐠',
		'🍎',
		'🍕',
		'🍪',
		'🍓',
		'🥕',
		'🎉',
		'🎊',
		'🎈',
		'🏆',
		'🥇'
	];

	interface Props {
		selected_question: number;
		check_choice?: boolean;
		data: EditorData;
	}

	let {
		selected_question = $bindable(),
		check_choice = false,
		data = $bindable()
	}: Props = $props();

	const set_answer_options = (new_answers: Answer[]) => {
		answers = new_answers;
		data.questions[selected_question] = {
			...data.questions[selected_question],
			type: check_choice ? QuizQuestionType.CHECK : QuizQuestionType.ABCD,
			answers
		};
	};

	let answers = $state<Answer[]>(
		Array.isArray(data.questions[selected_question].answers)
			? (data.questions[selected_question].answers as Answer[])
			: []
	);
	let emoji_picker_open_for = $state<number | undefined>();
	set_answer_options(answers);

	const normalize_answer_emoji = (answer: Answer) => {
		answer.emoji = answer.emoji?.trim() || undefined;
	};

	const set_answer_emoji = (answer: Answer, emoji?: string) => {
		answer.emoji = emoji;
		emoji_picker_open_for = undefined;
	};

	const toggle_emoji_picker = (index: number) => {
		emoji_picker_open_for = emoji_picker_open_for === index ? undefined : index;
	};

	const save_colors = (data_local: EditorData) => {
		if (selected_question === 0) {
			for (let i = 0; i < answers.length; i++) {
				localStorage.setItem(`quiz_color:${i}:${data_local.title}`, answers[i].color);
			}
		}
	};

	const get_empty_answer = (i: number): Answer => {
		return {
			answer: '',
			color: default_colors[i],
			right: false
		};
	};
	run(() => {
		save_colors(data);
	});
	const set_colors_if_unset = () => {
		for (let i = 0; i < answers.length; i++) {
			if (!answers[i].color) {
				answers[i].color = default_colors[i];
			}
		}
	};
	run(() => {
		set_colors_if_unset();
		data;
		selected_question;
	});
</script>

<div class="grid grid-rows-2 grid-flow-col auto-cols-auto gap-4 w-full px-10">
	{#if Array.isArray(answers)}
		{#each answers as answer, index}
			<div
				out:fade={{ duration: 150 }}
				class="p-4 rounded-lg flex justify-center w-full transition relative"
				class:bg-red-500={!answer.right}
				class:bg-green-500={answer.right}
				class:bg-yellow-500={!reach(ABCDQuestionSchema, 'answer').isValidSync(
					answer.answer
				)}
			>
				<button
					class="rounded-full absolute -top-2 -right-2 opacity-70 hover:opacity-100 transition"
					type="button"
					aria-label="Remove answer"
					onclick={() => {
						emoji_picker_open_for = undefined;
						answers.splice(index, 1);
						set_answer_options(answers);
					}}
				>
					<svg
						class="w-6 h-6 bg-red-500 rounded-full"
						fill="none"
						stroke="currentColor"
						viewBox="0 0 24 24"
						xmlns="http://www.w3.org/2000/svg"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
						/>
					</svg>
				</button>
				<input
					bind:value={answer.answer}
					type="text"
					class="border-b-2 border-dotted w-4/6 text-center rounded-lg bg-transparent outline-hidden focus:shadow-2xl transition-all"
					style="background-color: {answer.color}; color: {get_foreground_color(
						answer.color
					)}"
					placeholder={$t('editor.enter_answer')}
				/>
				<div class="relative mx-2">
					<button
						type="button"
						class="cq-surface cq-card-interactive flex h-10 w-11 items-center justify-center rounded-md text-lg transition focus:outline-hidden focus:ring-2 focus:ring-cq-brand"
						aria-label="Choose answer emoji"
						aria-expanded={emoji_picker_open_for === index}
						onclick={() => {
							toggle_emoji_picker(index);
						}}
					>
						<span class:text-cq-muted={!answer.emoji}>{answer.emoji || '🙂'}</span>
					</button>

					{#if emoji_picker_open_for === index}
						<div
							class="cq-card absolute left-1/2 top-12 z-40 w-56 -translate-x-1/2 rounded-md p-3"
							role="dialog"
							aria-label="Answer emoji picker"
						>
							<div class="mb-2 flex items-center justify-between gap-2">
								<span class="text-xs font-semibold uppercase tracking-wide text-cq-text">Emoji</span>
								<button
									type="button"
									class="cq-surface-muted rounded-full px-2 py-1 text-xs text-cq-muted transition hover:text-cq-text focus:outline-hidden focus:ring-2 focus:ring-cq-brand"
									onclick={() => {
										set_answer_emoji(answer);
									}}
								>
									Clear
								</button>
							</div>

							<div class="grid grid-cols-6 gap-1.5">
								{#each answer_emojis as emoji (emoji)}
									<button
										type="button"
										class="flex h-8 w-8 items-center justify-center rounded-md text-lg transition hover:bg-cq-brand/20 focus:outline-hidden focus:ring-2 focus:ring-cq-brand"
										class:cq-surface-muted={answer.emoji === emoji}
										aria-label="Use {emoji} emoji"
										onclick={() => {
											set_answer_emoji(answer, emoji);
										}}
									>
										{emoji}
									</button>
								{/each}
							</div>

							<input
								bind:value={answer.emoji}
								type="text"
								class="cq-surface-muted mt-3 w-full rounded-sm px-3 py-2 text-center text-cq-text outline-hidden transition-all placeholder:text-cq-muted focus:ring-2 focus:ring-cq-brand"
								placeholder="Paste custom emoji"
								aria-label="Custom answer emoji"
								onchange={() => {
									normalize_answer_emoji(answer);
								}}
								onkeydown={(event) => {
									if (event.key === 'Enter') {
										normalize_answer_emoji(answer);
										emoji_picker_open_for = undefined;
									}
								}}
							/>
						</div>
					{/if}
				</div>
				<button
					type="button"
					aria-label={answer.right ? 'Mark answer as incorrect' : 'Mark answer as correct'}
					onclick={() => {
						answer.right = !answer.right;
					}}
				>
					{#if answer.right}
						<svg
							class="w-6 h-6 inline-block"
							fill="none"
							stroke="currentColor"
							viewBox="0 0 24 24"
							xmlns="http://www.w3.org/2000/svg"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
							/>
						</svg>
					{:else}
						<svg
							class="w-6 h-6 inline-block"
							fill="none"
							stroke="currentColor"
							viewBox="0 0 24 24"
							xmlns="http://www.w3.org/2000/svg"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
							/>
						</svg>
					{/if}
				</button>
				<input
					class="rounded-lg p-1 border-cq-border border"
					type="color"
					bind:value={answer.color}
					oncontextmenu={preventDefault(() => {
						answer.color = default_colors[index];
					})}
				/>
			</div>
		{/each}
	{/if}
	{#if answers.length < 4}
		<button
			class="cq-surface cq-card-interactive p-4 rounded-lg transition"
			type="button"
			in:fade={{ duration: 150 }}
			onclick={() => {
				set_answer_options([...answers, { ...get_empty_answer(answers.length) }]);
			}}
		>
			<span class="italic text-center">{$t('editor_page.add_an_answer')}</span>
		</button>
	{/if}
</div>
