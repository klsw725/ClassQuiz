<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import { socket } from '$lib/socket';
	import { getLocalization } from '$lib/i18n';
	import { navbarVisible } from '$lib/stores.svelte.ts';
	import SomeAdminScreen from '$lib/admin.svelte';
	import GameNotStarted from '$lib/play/admin/game_not_started.svelte';
	import { onMount } from 'svelte';
	import FinalResults from '$lib/play/admin/final_results.svelte';
	import GrayButton from '$lib/components/buttons/gray.svelte';
	import { page } from '$app/state';
	import { SocketGameControls } from '$lib/play/admin/socket_game_controls.ts';
	import type { IGameState } from '$lib/play/admin/game_state.ts';
	import { QuizQuestionType, type QuizData } from '$lib/quiz_types';
	import type { Player, PlayerAnswer } from '$lib/admin';
	import { participantKey } from '$lib/admin';
	import { tinykeys } from '$lib/tinykeys';

	navbarVisible.visible = false;

	const { t } = getLocalization();

	// let gameData = {
	// 	game_id: 'a7ddb6af-79ab-45e0-b996-6254c1ad9818',
	// 	game_pin: '66190765'

	interface Props {
		// };
		data: any;
	}

	type RegisteredAsAdminPayload = {
		game_id?: string;
		game: string;
		players?: Player[];
		player_scores?: Record<string, number>;
		selected_question?: number;
		current_question?: number;
		question_show?: boolean;
		question_results?: unknown;
		answer_count?: number;
		timer_res?: string | number;
		game_started?: boolean;
	};

	class GameState implements IGameState {
		public game_id: string;
		public players: Player[];
		public player_scores: Record<string, number>;
		public selected_question: number;
		public timer_res: string;
		public question_results: any;
		public answer_count: number;
		public shown_question_now: number;
		public final_results: Array<null> | Array<Array<PlayerAnswer>>;
		public game_started: boolean;
		public quiz_data: QuizData;
		public control_visible: boolean;

		constructor(game_id: string) {
			this.game_id = game_id;
			this.players = $state([]);
			this.player_scores = $state({});
			this.selected_question = $state(-1);
			this.timer_res = $state(undefined);
			this.quiz_data = $state(null);
			this.control_visible = $state(true);
			this.shown_question_now = $state(-1);
			this.final_results = $state([null]);
			this.game_started = $state(false);
			this.question_results = $state(null);
			this.answer_count = $state(0);
		}

		is_game_ready_to_start(): boolean {
			return !this.game_started && this.players.length > 0;
		}

		is_game_starting(): boolean {
			return this.game_started && this.selected_question === -1;
		}

		is_active_question_last_question(): boolean {
			return this.selected_question + 1 === this.quiz_data.questions.length;
		}

		is_question_results_visible(): boolean {
			return this.timer_res === '0' && this.question_results !== null;
		}

		is_active_question_slide(): boolean {
			return (
				this.quiz_data?.questions?.[this.selected_question]?.type === QuizQuestionType.SLIDE
			);
		}

		is_question_ended(): boolean {
			return (
				this.timer_res === '0' &&
				this.question_results === null &&
				this.selected_question !== -1
			);
		}

		is_question_still_ongoing(): boolean {
			return this.timer_res !== '0' && this.selected_question !== -1;
		}
	}

	let { data }: Props = $props();
	let { auto_connect, game_token } = $state(data);
	const game_pin = data.game_pin;
	let errorMessage = $state('');
	let socketConnectionMessage = $state('');
	let socketErrorMessage = $state('');
	let success = $state(false);
	let dataexport_download_a = $state();
	let warnToLeave = true;
	let export_token = $state(undefined);
	let shouldRegisterWhenConnected = false;
	let registerAsAdminInProgress = false;

	const socket_game_controls: SocketGameControls = new SocketGameControls(socket);
	let game_state: GameState = $state(new GameState(game_token));
	const getPlayerDisplayNames = (players: Player[]): Record<string, string> => {
		const displayNames: Record<string, string> = {};
		for (const player of players) {
			if (player.zone) {
				displayNames[participantKey(player.username, player.zone)] =
					`${player.zone}-${player.username}`;
			}
		}
		return displayNames;
	};
	let player_display_names = $derived(getPlayerDisplayNames(game_state.players));

	const connect = async () => {
		if (success || registerAsAdminInProgress) {
			return;
		}

		if (!socket.connected) {
			shouldRegisterWhenConnected = true;
			socketConnectionMessage = $t('admin_page.connecting_to_socket');
			socket.connect();
			return;
		}

		shouldRegisterWhenConnected = false;
		registerAsAdminInProgress = true;
		socketErrorMessage = '';
		socketConnectionMessage = $t('admin_page.checking_host_session');
		try {
			socket.emit('register_as_admin', {
				game_pin: game_pin,
				game_id: game_token
			});
			await fetch(`/api/v1/quiz/play/check_captcha/${game_pin}`);
		} catch (e) {
			console.error('Failed to check game state while connecting as admin', e);
			if (!success && errorMessage === '') {
				socketErrorMessage = $t('admin_page.unable_to_check_game_info');
				socketConnectionMessage = $t('admin_page.check_network_and_retry');
			}
		} finally {
			registerAsAdminInProgress = false;
		}
	};

	const hydrateGameState = (data: RegisteredAsAdminPayload) => {
		if (data.game_id !== undefined) {
			game_state.game_id = data.game_id;
		}
		if (data.players !== undefined) {
			game_state.players = data.players;
		}
		if (data.player_scores !== undefined) {
			game_state.player_scores = data.player_scores;
		}

		const question_index = data.selected_question ?? data.current_question;
		if (question_index !== undefined) {
			game_state.selected_question = question_index;
			game_state.shown_question_now = question_index;
		}
		if (data.question_results !== undefined) {
			game_state.question_results = data.question_results;
		}
		if (data.answer_count !== undefined) {
			game_state.answer_count = data.answer_count;
		}
		if (data.timer_res !== undefined) {
			game_state.timer_res = data.timer_res.toString();
		} else if (data.question_show === false && question_index !== undefined) {
			game_state.timer_res = '0';
		}
		if (data.game_started !== undefined) {
			game_state.game_started = data.game_started;
		}
	};
	onMount(() => {
		const handleSocketConnect = () => {
			socketErrorMessage = '';
			socketConnectionMessage = '';
			if (shouldRegisterWhenConnected && !success) {
				void connect();
			}
		};
		const handleSocketConnectError = () => {
			if (success || (!auto_connect && !shouldRegisterWhenConnected)) {
				return;
			}
			socketErrorMessage = $t('admin_page.unable_to_connect_socket');
			socketConnectionMessage = $t('admin_page.retry_when_reconnected');
		};
		const handleSocketDisconnect = () => {
			registerAsAdminInProgress = false;
			if (success || (!auto_connect && !shouldRegisterWhenConnected)) {
				return;
			}
			shouldRegisterWhenConnected = true;
			socketErrorMessage = '';
			socketConnectionMessage = $t('admin_page.socket_disconnected_reconnecting');
		};

		const handleGameNotFound = () => {
			shouldRegisterWhenConnected = false;
			errorMessage = $t('admin_page.game_not_found');
		};
		const handleSocketError = () => {
			shouldRegisterWhenConnected = false;
			errorMessage = $t('admin_page.error');
		};

		socket.on('connect', handleSocketConnect);
		socket.on('connect_error', handleSocketConnectError);
		socket.on('disconnect', handleSocketDisconnect);
		socket.on('game_not_found', handleGameNotFound);
		socket.on('error', handleSocketError);

		if (auto_connect) {
			void connect();
		}
		tinykeys(window, {
			Enter: next_action,
			Space: next_action
		});

		return () => {
			socket.off('connect', handleSocketConnect);
			socket.off('connect_error', handleSocketConnectError);
			socket.off('disconnect', handleSocketDisconnect);
			socket.off('game_not_found', handleGameNotFound);
			socket.off('error', handleSocketError);
		};
	});
	socket.on('session_id', (_d) => {});

	socket.on('registered_as_admin', (data: RegisteredAsAdminPayload) => {
		game_state.quiz_data = JSON.parse(data.game);
		game_state.game_started = Boolean(game_state.quiz_data.started);
		hydrateGameState(data);
		console.log(game_state.quiz_data);
		socketConnectionMessage = '';
		socketErrorMessage = '';
		shouldRegisterWhenConnected = false;
		success = true;
	});
	socket.on('player_joined', (int_data) => {
		game_state.players = [...game_state.players, int_data];
	});
	socket.on('player_left', (data: Player) => {
		const left_player_key = participantKey(data.username, data.zone);
		game_state.players = game_state.players.filter(
			(player) => participantKey(player.username, player.zone) !== left_player_key
		);
	});
	socket.on('already_registered_as_admin', () => {
		shouldRegisterWhenConnected = false;
		// eslint-disable-next-line @typescript-eslint/ban-ts-comment
		// @ts-ignore
		errorMessage = $t('admin_page.already_registered_as_admin');
	});
	socket.on('start_game', (_) => {
		game_state.game_started = true;
	});

	socket.on('control_visibility', (data) => {
		game_state.control_visible = data.visible;
	});

	/*	socket.on('question_results', (int_data) => {
        try {
            int_data = JSON.parse(int_data);
        } catch (e) {
            console.error('Failed to parse question results');
            return;
        }
        question_results = int_data;
    });*/
	socket.on('export_token', (int_data) => {
		warnToLeave = false;
		export_token = int_data;

		setTimeout(() => {
			warnToLeave = true;
		}, 200);
	});

	socket.on('results_saved_successfully', (_) => {
		results_saved = true;
	});

	const confirmUnload = () => {
		if (warnToLeave) {
			event.preventDefault();
			// eslint-disable-next-line @typescript-eslint/ban-ts-comment
			// @ts-ignore
			event.returnValue = '';
		}
	};

	const request_answer_export = (e: Event) => {
		e.preventDefault();
		socket.emit('get_export_token');
	};
	const save_quiz = () => {
		socket.emit('save_quiz');
	};

	let bg_color = $derived(
		game_state.quiz_data ? game_state.quiz_data.background_color : undefined
	);
	let bg_image = $derived(
		game_state.quiz_data ? game_state.quiz_data.background_image : undefined
	);
	let results_saved = $state(false);

	let show_final_results = $derived(
		JSON.stringify(game_state.final_results) !== JSON.stringify([null])
	);

	// This function in called in every keyboard event in this page
	const next_action = () => {
		if (
			game_state.is_active_question_last_question() &&
			(game_state.is_question_results_visible() || game_state.is_active_question_slide())
		) {
			socket_game_controls.get_final_results();
		} else if (
			game_state.is_game_starting() ||
			game_state.is_question_results_visible() ||
			game_state.is_active_question_slide()
		) {
			socket_game_controls.set_question_number(game_state.selected_question + 1);
		} else if (game_state.is_question_still_ongoing()) {
			socket_game_controls.show_solutions();
			game_state.timer_res = '0';
		} else if (game_state.is_question_ended()) {
			socket_game_controls.get_question_results(game_token, game_state.shown_question_now);
		} else {
			console.warn('No action available for this event');
		}
	};
</script>

<svelte:window onbeforeunload={confirmUnload} />
<svelte:head>
	<title>ClassQuiz - 호스트</title>
</svelte:head>
<div
	class="min-h-screen min-w-full"
	style="background-repeat: no-repeat;background-size: 100% 100%;background-image: {bg_image
		? `url('${bg_image}')`
		: `unset`}; background-color: {bg_color ? bg_color : 'transparent'}"
	class:text-black={bg_color}
>
	{#if JSON.stringify(game_state.final_results) !== JSON.stringify([null])}
		{#if game_state.control_visible}
			<div class="w-screen flex justify-center mt-16">
				<div class="w-fit">
					{#if export_token === undefined}
						<GrayButton onclick={request_answer_export}
							>{$t('admin_page.request_export_results')}</GrayButton
						>
					{:else}
						<GrayButton
							target="_blank"
							href="/api/v1/quiz/export_data/{export_token}?ts={new Date().getTime()}&game_pin={game_pin}"
							>{$t('admin_page.download_export_results')}</GrayButton
						>
					{/if}
				</div>
			</div>
			<div class="w-screen flex justify-center mt-2">
				<div class="w-fit">
					<GrayButton onclick={save_quiz} flex={true} disabled={results_saved}>
						{#if results_saved}
							<svg
								class="w-4 h-4"
								aria-hidden="true"
								fill="none"
								stroke="currentColor"
								stroke-width="2"
								viewBox="0 0 24 24"
								xmlns="http://www.w3.org/2000/svg"
							>
								<path
									d="M5 13l4 4L19 7"
									stroke-linecap="round"
									stroke-linejoin="round"
								/>
							</svg>
						{:else}{$t('admin_page.save_results')}{/if}
					</GrayButton>
				</div>
			</div>
			<div class="w-screen flex justify-center mt-2">
				<div class="w-fit">
					<GrayButton href="/dashboard">{$t('words.dashboard')}</GrayButton>
				</div>
			</div>
		{/if}
		<FinalResults
			bind:data={game_state.player_scores}
			{show_final_results}
			display_names={player_display_names}
		/>
	{/if}
	{#if !success}
		{#if errorMessage !== ''}
			<p class="text-red-700">{errorMessage}</p>
		{:else if socketErrorMessage !== ''}
			<div class="flex min-h-screen items-center justify-center px-4 text-cq-text">
				<div class="cq-card w-full max-w-md p-6 text-center">
					<p class="text-xl font-semibold text-cq-text">{socketErrorMessage}</p>
					<p class="mt-2 text-cq-muted">{socketConnectionMessage}</p>
				</div>
			</div>
		{:else if auto_connect}
			<div class="flex min-h-screen items-center justify-center px-4 text-cq-text">
				<div class="cq-card w-full max-w-md p-6 text-center">
					<p class="text-xl font-semibold text-cq-text">
						{$t('admin_page.connecting_to_host_session')}
					</p>
					<p class="mt-2 text-cq-muted">
						{socketConnectionMessage || $t('admin_page.please_wait')}
					</p>
				</div>
			</div>
		{/if}
	{:else if !game_state.game_started}
		<GameNotStarted
			{game_pin}
			bind:game_state
			{socket_game_controls}
			cqc_code={page.url.searchParams.get('cqc_code')}
		/>
	{:else}
		<SomeAdminScreen {game_token} {bg_color} bind:game_state />
	{/if}
</div>
<a
	onclick={request_answer_export}
	href="#"
	target="_blank"
	bind:this={dataexport_download_a}
	download=""
	class="absolute -top-3/4 -left-3/4 opacity-0">다운로드</a
>
