<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<!--suppress ALL -->
<script lang="ts">
	import { socket } from '$lib/socket';
	import JoinGame from '$lib/play/join.svelte';
	import type { Question as QuestionType } from '$lib/quiz_types';
	import ShowTitle from '$lib/play/title.svelte';
	import QuestionComponent from '$lib/play/question.svelte';
	import { navbarVisible } from '$lib/stores.svelte.ts';
	import ShowEndScreen from '$lib/play/admin/final_results.svelte';
	import KahootResults from '$lib/play/results_kahoot.svelte';
	import { getLocalization } from '$lib/i18n';
	import { participantKey } from '$lib/admin';
	import { browser } from '$app/environment';
	import Cookies from 'js-cookie';
	const { t } = getLocalization();

	interface Props {
		// Exports
		data: { game_pin: string };
	}

	let { data }: Props = $props();
	let { game_pin } = $state(data);
	const initial_game_pin = data.game_pin;
	const joined_game_cookie_expires = 2 / 24;

	// Types
	interface GameMeta {
		started: boolean;
	}

	interface CheckCaptchaResponse {
		game_mode: string;
	}

	interface GameData {
		game_id: string;
		started?: boolean;
		title: string;
		description: string;
		cover_image?: string;
		background_color?: string;
	}

	interface SetQuestionNumberPayload {
		question: QuestionType;
		question_index: string;
	}

	interface AnswerDetail {
		answer: string;
		matched: boolean;
	}

	interface QuestionResult {
		username: string;
		answer: string;
		answer_details?: AnswerDetail[];
		right: boolean;
		time_taken: number;
		score: number;
		zone?: string;
	}

	let game_mode: string | undefined = $state();
	let final_results: Array<null> | Record<string, PlayerAnswer[]> = $state([null]);

	interface PlayerAnswer {
		username: string;
		answer: string;
		right: string;
		zone?: string;
	}

	interface JoinedGameCookie {
		sid: string;
		username: string;
		game_pin: string;
		zone?: string;
	}

	type ScreenWakeLockSentinel = EventTarget & {
		release: () => Promise<void>;
	};

	type NavigatorWithWakeLock = Navigator & {
		wakeLock?: {
			request: (_type: 'screen') => Promise<ScreenWakeLockSentinel>;
		};
	};

	// Variables init
	let question_index: string = $state('');
	let unique: object = $state({});
	navbarVisible.visible = false;
	let answer_results: QuestionResult[] | null | undefined = $state();
	let gameData: GameData | undefined = $state();
	let solution: QuestionType | undefined = $state();
	let username = $state('');
	let zone = $state('1구역');
	let scores: Record<string, number> = $state({});
	let display_names: Record<string, string> = $state({});
	let current_participant_key = $derived(participantKey(username, zone));
	let gameMeta: GameMeta = $state({
		started: false
	});
	let playWakeLockActive = $derived(
		gameData !== undefined && JSON.stringify(final_results) === JSON.stringify([null])
	);
	let wakeLockRouteActive = true;
	let wakeLockSentinel: ScreenWakeLockSentinel | undefined;
	let wakeLockRequestPending = false;

	let question: QuestionType | undefined = $state();

	let preventReload = true;

	// Functions
	function restart() {
		unique = {};
	}

	const rememberDisplayNames = (results: Array<PlayerAnswer | QuestionResult | null>) => {
		const nextDisplayNames = { ...display_names };
		for (const result of results) {
			if (result?.zone) {
				nextDisplayNames[participantKey(result.username, result.zone)] =
					`${result.zone}-${result.username}`;
			}
		}
		display_names = nextDisplayNames;
	};

	const restoreJoinedGameState = (data: JoinedGameCookie) => {
		username = data.username;
		game_pin = data.game_pin;
		if (data.zone) {
			zone = data.zone;
			display_names = {
				...display_names,
				[participantKey(data.username, data.zone)]: `${data.zone}-${data.username}`
			};
		}
	};

	const is_reload_navigation = () => {
		if (!browser) {
			return false;
		}
		const [navigation_entry] = performance.getEntriesByType(
			'navigation'
		) as PerformanceNavigationTiming[];
		return navigation_entry?.type === 'reload';
	};

	const should_restore_joined_game = (joined_game: JoinedGameCookie) => {
		if (initial_game_pin !== '') {
			return joined_game.game_pin === initial_game_pin;
		}
		return is_reload_navigation();
	};

	// Block refresh while the game is in progress (but leave tab/window closing alone).
	// beforeunload can't tell refresh from close and can't actually prevent a reload,
	// so we intercept the refresh shortcuts directly instead.
	const blockRefreshKeys = (event: KeyboardEvent) => {
		if (!preventReload) {
			return;
		}
		const key = event.key;
		const isReloadCombo =
			key === 'F5' || ((event.ctrlKey || event.metaKey) && (key === 'r' || key === 'R'));
		if (isReloadCombo) {
			event.preventDefault();
		}
	};

	const handleWakeLockRelease = (event: Event) => {
		if (event.currentTarget === wakeLockSentinel) {
			wakeLockSentinel.removeEventListener('release', handleWakeLockRelease);
			wakeLockSentinel = undefined;
		}
	};

	const releaseScreenWakeLock = async () => {
		const sentinel = wakeLockSentinel;
		if (!sentinel) {
			return;
		}
		wakeLockSentinel = undefined;
		sentinel.removeEventListener('release', handleWakeLockRelease);
		try {
			await sentinel.release();
		} catch {
			return;
		}
	};

	const requestScreenWakeLock = async () => {
		if (
			!browser ||
			!wakeLockRouteActive ||
			wakeLockSentinel ||
			wakeLockRequestPending ||
			!('wakeLock' in navigator) ||
			document.visibilityState !== 'visible'
		) {
			return;
		}
		const wakeLock = (navigator as NavigatorWithWakeLock).wakeLock;
		if (!wakeLock) {
			return;
		}
		wakeLockRequestPending = true;
		try {
			const sentinel = await wakeLock.request('screen');
			if (
				!wakeLockRouteActive ||
				!playWakeLockActive ||
				document.visibilityState !== 'visible'
			) {
				await sentinel.release();
				return;
			}
			sentinel.addEventListener('release', handleWakeLockRelease);
			wakeLockSentinel = sentinel;
		} catch {
			return;
		} finally {
			wakeLockRequestPending = false;
		}
	};

	const handleVisibilityChange = () => {
		if (document.visibilityState === 'visible' && playWakeLockActive) {
			void requestScreenWakeLock();
		}
	};

	$effect(() => {
		if (playWakeLockActive) {
			void requestScreenWakeLock();
		} else {
			void releaseScreenWakeLock();
		}
	});

	$effect(() => {
		if (!browser) {
			return;
		}
		document.addEventListener('visibilitychange', handleVisibilityChange);
		return () => {
			wakeLockRouteActive = false;
			document.removeEventListener('visibilitychange', handleVisibilityChange);
			void releaseScreenWakeLock();
		};
	});

	// Trap the mobile/browser back button while the game is in progress.
	// beforeunload doesn't reliably catch back navigation on mobile,
	// so we push a dummy history entry and re-push it whenever the user pops it.
	$effect(() => {
		if (!browser) {
			return;
		}
		history.pushState(null, '', location.href);
		const onPopState = () => {
			if (preventReload) {
				history.pushState(null, '', location.href);
			}
		};
		window.addEventListener('popstate', onPopState);
		window.addEventListener('keydown', blockRefreshKeys);
		// Stop mobile "pull-to-refresh" gesture.
		const previousOverscroll = document.body.style.overscrollBehaviorY;
		document.body.style.overscrollBehaviorY = 'contain';
		return () => {
			window.removeEventListener('popstate', onPopState);
			window.removeEventListener('keydown', blockRefreshKeys);
			document.body.style.overscrollBehaviorY = previousOverscroll;
		};
	});

	socket.on('time_sync', (data) => {
		socket.emit('echo_time_sync', data);
	});

	socket.on('connect', async () => {
		console.log('Connected!');
		const cookie_data = Cookies.get('joined_game');
		if (!cookie_data) {
			return;
		}
		const data = JSON.parse(cookie_data) as JoinedGameCookie;
		if (!should_restore_joined_game(data)) {
			Cookies.remove('joined_game');
			return;
		}
		socket.emit('rejoin_game', {
			old_sid: data.sid,
			username: data.username,
			game_pin: data.game_pin,
			zone: data.zone
		});
		const res = await fetch(`/api/v1/quiz/play/check_captcha/${data.game_pin}`);
		const json: CheckCaptchaResponse = await res.json();
		game_mode = json.game_mode;
	});

	// Socket-events
	socket.on('joined_game', (data: GameData) => {
		gameData = data;
		// eslint-disable-next-line no-undef
		plausible('Joined Game', { props: { game_id: gameData.game_id } });
		display_names = {
			...display_names,
			[participantKey(username, zone)]: `${zone}-${username}`
		};
		Cookies.set('joined_game', JSON.stringify({ sid: socket.id, username, game_pin, zone }), {
			expires: joined_game_cookie_expires
		});
	});
	socket.on('rejoined_game', (data: GameData) => {
		const cookie_data = Cookies.get('joined_game');
		if (cookie_data) {
			const joinedGame = JSON.parse(cookie_data) as JoinedGameCookie;
			restoreJoinedGameState(joinedGame);
			Cookies.set('joined_game', JSON.stringify({ ...joinedGame, sid: socket.id }), {
				expires: joined_game_cookie_expires
			});
		}
		gameData = data;
		if (data.started) {
			gameMeta.started = true;
		}
	});

	socket.on('participant_already_connected', () => {
		window.alert($t('play_page.participant_already_connected'));
	});

	socket.on('game_not_found', () => {
		const cookie_data = Cookies.get('joined_game');
		if (cookie_data) {
			Cookies.remove('joined_game');
			window.location.reload();
			return;
		}
	});

	socket.on('set_question_number', (data: SetQuestionNumberPayload) => {
		solution = undefined;
		restart();
		question = data.question;
		question_index = data.question_index;
		answer_results = undefined;
	});

	socket.on('start_game', () => {
		gameMeta.started = true;
	});

	socket.on('question_results', (data: QuestionResult[] | null) => {
		restart();
		if (data) {
			rememberDisplayNames(data);
		}
		answer_results = data;
	});

	socket.on('question_player_scores', (data: Record<string, number>) => {
		scores = data;
	});

	socket.on('username_already_exists', () => {
		window.alert($t('play_page.username_already_exists'));
	});

	socket.on('kick', () => {
		window.alert($t('play_page.kicked'));
		preventReload = false;
		game_pin = '';
		username = '';
		Cookies.remove('joined_game');
		window.location.reload();
	});
	socket.on('final_player_scores', (data: Record<string, number>) => {
		scores = data;
	});

	socket.on('final_results', (data: Record<string, PlayerAnswer[]>) => {
		for (const questionResults of Object.values(data)) {
			rememberDisplayNames(questionResults);
		}
		final_results = data;
		Cookies.remove('joined_game');
	});

	socket.on('solutions', (data: QuestionType) => {
		solution = data;
	});

	let bg_color = $derived(gameData ? gameData.background_color : undefined);

	// The rest
</script>

<svelte:head>
	<title>ClassQuiz - {$t('words.play')}</title>
</svelte:head>
<div
	class="min-h-svh min-w-full"
	style="background: {bg_color ? bg_color : 'transparent'}"
	class:text-cq-text={bg_color}
>
	<div>
		{#if !gameMeta.started && gameData === undefined}
			<JoinGame bind:game_pin bind:game_mode bind:username bind:zone />
		{:else if JSON.stringify(final_results) !== JSON.stringify([null])}
			<ShowEndScreen
				bind:data={scores}
				show_final_results={true}
				username={current_participant_key}
				{display_names}
			/>
		{:else if gameData !== undefined && question_index === ''}
			<ShowTitle
				title={gameData.title}
				description={gameData.description}
				cover_image={gameData.cover_image}
			/>
		{:else if gameMeta.started && gameData !== undefined && question !== undefined && question_index !== '' && answer_results === undefined}
			{#key unique}
				<div class="text-cq-text">
					<QuestionComponent bind:game_mode bind:question {question_index} {solution} />
				</div>
			{/key}
		{:else if gameMeta.started && answer_results !== undefined}
			{#if answer_results === null}
				<div class="w-full flex justify-center">
					<h1 class="text-3xl">{$t('admin_page.no_answers')}</h1>
				</div>
			{:else}
				{#key unique}
					<KahootResults
						username={current_participant_key}
						question_results={answer_results}
						{scores}
						bind:display_names
					/>
				{/key}
			{/if}
		{/if}
	</div>
</div>
