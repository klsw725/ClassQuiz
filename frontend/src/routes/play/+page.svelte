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
	import Cookies from 'js-cookie';
	const { t } = getLocalization();

	interface Props {
		// Exports
		data: { game_pin: string };
	}

	let { data }: Props = $props();
	let { game_pin } = $state(data);

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

	interface QuestionResult {
		username: string;
		answer: string;
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

	const confirmUnload = (event: BeforeUnloadEvent) => {
		if (preventReload) {
			event.preventDefault();
			event.returnValue = '';
		}
	};

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
		restoreJoinedGameState(data);
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
			expires: 3600
		});
	});
	socket.on('rejoined_game', (data: GameData) => {
		const cookie_data = Cookies.get('joined_game');
		if (cookie_data) {
			const joinedGame = JSON.parse(cookie_data) as JoinedGameCookie;
			restoreJoinedGameState(joinedGame);
			Cookies.set('joined_game', JSON.stringify({ ...joinedGame, sid: socket.id }), {
				expires: 3600
			});
		}
		gameData = data;
		if (data.started) {
			gameMeta.started = true;
		}
	});

	socket.on('participant_already_connected', () => {
		window.alert(
			'이 게임은 이미 다른 탭이나 기기에서 열려 있습니다. 활성 세션을 사용하거나 닫은 뒤 다시 연결하세요.'
		);
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

	socket.on('username_already_exists', () => {
		window.alert('이미 사용 중인 이름입니다!');
	});

	socket.on('kick', () => {
		window.alert('강퇴되었습니다');
		preventReload = false;
		game_pin = '';
		username = '';
		Cookies.remove('joined_game');
		window.location.reload();
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

<svelte:window onbeforeunload={confirmUnload} />
<svelte:head>
	<title>ClassQuiz - 플레이</title>
</svelte:head>
<div
	class="min-h-screen min-w-full"
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
				<div>
					<h2 class="text-center text-3xl mb-8">{$t('words.result', { count: 2 })}</h2>
				</div>
				{#key unique}
					<KahootResults
						username={current_participant_key}
						question_results={answer_results}
						bind:scores
						bind:display_names
					/>
				{/key}
			{/if}
		{/if}
	</div>
</div>
