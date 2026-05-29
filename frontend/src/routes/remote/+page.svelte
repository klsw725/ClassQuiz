<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import { page } from '$app/state';
	import { socket } from '$lib/socket';
	import type { Answer, QuizData, VotingAnswer } from '$lib/quiz_types';
	import { QuizQuestionType } from '$lib/quiz_types.js';
	import Spinner from '$lib/Spinner.svelte';
	import CircularTimer from '$lib/play/circular_progress.svelte';
	import { getLocalization } from '$lib/i18n';
	import { participantKey } from '$lib/admin';
	import { navbarVisible } from '$lib/stores.svelte.ts';
	import MediaComponent from '$lib/editor/MediaComponent.svelte';

	const data = {
		game_pin: page.url.searchParams.get('game_pin'),
		game_id: page.url.searchParams.get('game_id')
	};

	navbarVisible.visible = false;

	const { t } = getLocalization();
	const get_answer_options = (
		question: QuizData['questions'][number]
	): Array<Answer | VotingAnswer> =>
		Array.isArray(question.answers) ? (question.answers as Array<Answer | VotingAnswer>) : [];
	let timer_interval: NodeJS.Timeout;
	let timer_res = $state(undefined);
	let selected_question = $state(-1);
	let game_started = $state(false);
	let question_results = $state();
	let final_results = $state([null]);
	let warnToLeave = true;
	let dataexport_download_a: HTMLAnchorElement = $state();

	let players: Array<{ sid: string; username: string; zone?: string }> = $state([]);
	const LOBBY_VISIBLE_PLAYER_LIMIT = 80;
	const formatPlayerName = (player: { username: string; zone?: string }) =>
		player.zone ? `${player.zone}-${player.username}` : player.username;
	let visible_lobby_player_count = $state(LOBBY_VISIBLE_PLAYER_LIMIT);
	let visible_lobby_players = $derived(players.slice(0, visible_lobby_player_count));
	let hidden_lobby_player_count = $derived(
		Math.max(players.length - visible_lobby_players.length, 0)
	);

	let game_data: QuizData = $state();
	let shown_question_now: number;
	let control_visible = $state(false);

	if (!data.game_id || !data.game_pin) {
		console.log('Error!');
	} else {
		socket.emit('register_as_remote', data);
	}

	const timer = (time: string) => {
		let seconds = Number(time);
		timer_interval = setInterval(() => {
			if (timer_res === '0') {
				clearInterval(timer_interval);
				// socket.emit('show_solutions', {});
				return;
			} else {
				seconds--;
			}

			timer_res = seconds.toString();
		}, 1000);
	};

	const confirmUnload = (e: BeforeUnloadEvent) => {
		if (warnToLeave) {
			e.preventDefault();
			e.returnValue = '';
		}
	};

	const set_question_number = (q_number: number) => {
		socket.emit('set_question_number', q_number.toString());
	};

	const start_game = () => {
		socket.emit('start_game', '');
	};

	const get_question_results = () => {
		socket.emit('get_question_results', {
			question_number: shown_question_now
		});
	};

	const show_solutions = () => {
		socket.emit('show_solutions', {});
	};
	const get_final_results = () => {
		socket.emit('get_final_results', {});
	};

	const request_answer_export = async (e: Event) => {
		e.preventDefault();
		socket.emit('get_export_token');
	};

	const get_already_joined_players = async () => {
		const res = await fetch(
			`/api/v1/live/players?game_pin=${data.game_pin}&game_id=${data.game_id}`
		);
		if (res.ok) {
			players = await res.json();
		}
	};
	let circular_progress = $derived.by(() => {
		try {
			return (
				1 -
				((100 / parseInt(game_data.questions[selected_question].time)) *
					parseInt(timer_res)) /
					100
			);
		} catch {
			return 0;
		}
	});

	socket.on('solutions', (_) => {
		timer_res = '0';
		clearInterval(timer_interval);
	});
	socket.on('question_results', (_) => {
		timer_res = '0';
		clearInterval(timer_interval);
	});
	socket.on('registered_as_admin', (data) => {
		game_data = JSON.parse(data.game);
	});

	socket.on('start_game', (_) => {
		game_started = true;
	});

	socket.on('control_visibility', (data) => {
		control_visible = data.visible;
	});

	socket.on('question_results', (data) => {
		try {
			question_results = JSON.parse(data);
			timer_res = '0';
		} catch {
			question_results = undefined;
		}
	});
	socket.on('set_question_number', (data) => {
		timer_res = '0';
		clearInterval(timer_interval);
		question_results = null;
		shown_question_now = data.question_index;
		timer_res = game_data.questions[data.question_index].time;
		selected_question = selected_question + 1;
		timer(timer_res);
	});

	socket.on('final_results', (data) => {
		// data = JSON.parse(data);
		final_results = data;
	});

	socket.on('everyone_answered', (_) => {
		timer_res = '0';
	});

	socket.on('export_token', (int_data) => {
		warnToLeave = false;
		dataexport_download_a.href = `/api/v1/quiz/export_data/${int_data}?ts=${new Date().getTime()}&game_pin=${
			game_data.game_pin
		}`;
		dataexport_download_a.click();
		setTimeout(() => {
			warnToLeave = true;
		}, 200);
	});

	socket.on('player_joined', (data) => {
		players = [...players, data];
	});
	socket.on('player_left', (data: { username: string; zone?: string }) => {
		const left_player_key = participantKey(data.username, data.zone);
		players = players.filter(
			(player) => participantKey(player.username, player.zone) !== left_player_key
		);
	});
</script>

<svelte:window onbeforeunload={confirmUnload} />
{#if game_started}
	{#if selected_question + 1 === game_data.questions.length && ((timer_res === '0' && question_results !== null) || game_data?.questions?.[selected_question]?.type === QuizQuestionType.SLIDE)}
		{#if JSON.stringify(final_results) === JSON.stringify([null])}
			<button onclick={get_final_results} class="accent-button m-4 w-fit"
				>최종 결과 보기
			</button>
		{:else}
			<div class="w-screen flex justify-center mt-16">
				<button onclick={request_answer_export} class="accent-button w-fit"
					>{$t('admin_page.export_results')}</button
				>
			</div>
		{/if}
	{:else if timer_res === '0' || selected_question === -1}
		{#if (selected_question + 1 !== game_data.questions.length && question_results !== null) || selected_question === -1}
			<button
				onclick={() => {
					set_question_number(selected_question + 1);
				}}
				class="accent-button m-4 w-fit"
				>다음 문제 ({selected_question + 2})
			</button>
		{/if}
		{#if question_results === null && selected_question !== -1}
			{#if game_data.questions[selected_question].type === QuizQuestionType.SLIDE}
				<button
					onclick={() => {
						set_question_number(selected_question + 1);
					}}
					class="accent-button m-4 w-fit"
					>다음 문제 ({selected_question + 2})
				</button>
			{:else}
				<button onclick={get_question_results} class="action-button m-4 w-fit"
					>결과 보기
				</button>
			{/if}
		{/if}
	{:else if selected_question !== -1}
		{#if game_data.questions[selected_question].type === QuizQuestionType.SLIDE}
			<button
				onclick={() => {
					set_question_number(selected_question + 1);
				}}
				class="accent-button m-4 w-fit"
				>다음 문제 ({selected_question + 2})
			</button>
		{:else}
			<button onclick={show_solutions} class="action-button m-4 w-fit"
				>시간을 멈추고 해설 보기
			</button>
		{/if}
	{/if}
	{#if selected_question === -1}
		<div class="cq-card m-4 p-6 text-cq-text">
			<h1 class="text-4xl font-bold notranslate" translate="no">{game_data.title}</h1>
			<p class="mt-2 text-cq-muted notranslate" translate="no">{game_data.description}</p>
		</div>
	{:else if game_data.questions[selected_question].type === QuizQuestionType.SLIDE}
		{#await import('$lib/play/admin/slide.svelte')}
			<Spinner my_20={false} />
		{:then c}
			<c.default question={game_data.questions[selected_question]} />
		{/await}
	{:else}
		<div class="cq-card m-4 flex flex-col justify-center p-4 text-cq-text">
			<h1 class="text-6xl text-center font-semibold notranslate" translate="no">
				{@html game_data.questions[selected_question].question}
			</h1>
			<!--			<span class='text-center py-2 text-lg'>{$t('admin_page.time_left')}: {timer_res}</span>-->
			<div class="mx-auto my-2">
				<CircularTimer text={timer_res} progress={circular_progress} color="#ef4444" />
			</div>
			{#if game_data.questions[selected_question].image}
				<div>
					<MediaComponent
						src={game_data.questions[selected_question].image}
						muted={false}
						css_classes="max-h-[20vh] object-cover mx-auto mb-8 w-auto"
					/>
				</div>
			{/if}
			{#if (game_data.questions[selected_question].type === QuizQuestionType.ABCD || game_data.questions[selected_question].type === QuizQuestionType.VOTING || game_data.questions[selected_question].type === QuizQuestionType.CHECK) && Array.isArray(game_data.questions[selected_question].answers)}
				{@const answer_options = get_answer_options(game_data.questions[selected_question])}
				<div class="grid grid-cols-2 gap-2 w-full p-4">
					{#each answer_options as answer, _i}
						<div
							class="cq-card h-fit flex"
							style="background-color: {answer.color ?? '#B45309'}"
							class:opacity-50={'right' in answer &&
								!answer.right &&
								game_data.questions[selected_question].type ===
									QuizQuestionType.ABCD}
						>
							<span
								class="text-center text-2xl px-2 py-4 w-full text-black notranslate"
								translate="no"
							>
								{#if answer.emoji}
									<span class="mr-2" aria-label="답변 이모지"
										>{answer.emoji}</span
									>
								{/if}
								{answer.answer}
							</span>
							<span class="pl-4 w-10"></span>
						</div>
					{/each}
				</div>
			{/if}
		</div>
	{/if}

	{#if timer_res === '0' && JSON.stringify(final_results) === JSON.stringify( [null] ) && game_data.questions[selected_question].type !== QuizQuestionType.SLIDE}
		{#if game_data.questions[selected_question].type === QuizQuestionType.VOTING && question_results}
			{#await import('$lib/play/admin/voting_results.svelte')}
				<Spinner />
			{:then c}
				<c.default
					data={question_results}
					question={game_data.questions[selected_question]}
				/>
			{/await}
		{/if}
	{/if}
{:else}
	<div class="flex min-h-screen items-center justify-center px-4 text-cq-text">
		<div class="cq-card w-full max-w-md p-6 text-center">
			<button onclick={start_game} class="accent-button w-fit">게임 시작!</button>

			<h2 class="mt-6 text-xl font-semibold text-cq-text">플레이어:</h2>
			{#await get_already_joined_players()}
				<Spinner my_20={false} />
			{:then _}
				<div class="cq-surface-muted mt-3 p-3 text-cq-muted">
					<ul>
						{#each visible_lobby_players as player (participantKey(player.username, player.zone))}
							<li>{formatPlayerName(player)}</li>
						{/each}
					</ul>
					{#if hidden_lobby_player_count > 0}
						<button
							type="button"
							class="cq-surface mt-3 w-full p-2 font-semibold text-cq-muted hover:text-cq-text transition"
							onclick={() =>
								(visible_lobby_player_count += LOBBY_VISIBLE_PLAYER_LIMIT)}
						>
							+{Math.min(LOBBY_VISIBLE_PLAYER_LIMIT, hidden_lobby_player_count)}
						</button>
					{/if}
				</div>
			{/await}
		</div>
	</div>
{/if}
<div class="fixed top-0 right-0 p-3">
	{#if control_visible}
		<button
			class="action-button w-fit"
			onclick={() => {
				socket.emit('set_control_visibility', { visible: false });
			}}
			>컨트롤 숨기기
		</button>
	{:else}
		<button
			class="action-button w-fit"
			onclick={() => {
				socket.emit('set_control_visibility', { visible: true });
			}}
			>컨트롤 보이기
		</button>
	{/if}
</div>

<a
	onclick={request_answer_export}
	href="#"
	bind:this={dataexport_download_a}
	class="absolute -top-3/4 -left-3/4 opacity-0 hidden">다운로드</a
>
