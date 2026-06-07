<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import ControllerCodeDisplay from '$lib/components/controller/code.svelte';
	import { getLocalization } from '$lib/i18n';
	import GrayButton from '$lib/components/buttons/gray.svelte';
	import { fade } from 'svelte/transition';
	import { SocketGameControls } from '$lib/play/admin/socket_game_controls.ts';
	import type { GameState } from '$lib/play/admin/game_state';
	import { participantKey, type Player } from '$lib/admin';

	interface Props {
		game_pin: string;
		game_state: GameState;
		socket_game_controls: SocketGameControls;
		cqc_code: string;
	}

	let {
		game_pin,
		game_state = $bindable(),
		socket_game_controls,
		cqc_code = $bindable()
	}: Props = $props();

	const LOBBY_VISIBLE_PLAYER_LIMIT = 80;
	const lobby_zones = Array.from({ length: 11 }, (_, index) => `${index + 1}구역`);

	let fullscreen_open = $state(false);
	const { t } = getLocalization();
	const formatPlayerName = (player: { username: string; zone?: string }) =>
		player.zone ? `${player.zone}-${player.username}` : player.username;
	const groupLobbyPlayersByZone = (players: Array<Player>) => {
		const groups: Array<{ key: string; zone: string; players: Array<Player> }> = lobby_zones.map(
			(zone) => ({
				key: zone,
				zone,
				players: []
			})
		);
		const players_without_zone: Array<Player> = [];

		for (const player of players) {
			if (!player.zone) {
				players_without_zone.push(player);
				continue;
			}

			const zone_key = player.zone;
			const group = groups.find((group) => group.key === zone_key);

			if (group !== undefined) {
				group.players.push(player);
			}
		}

		if (players_without_zone.length > 0) {
			groups.push({
				key: '',
				zone: $t('words.zone'),
				players: players_without_zone
			});
		}

		return groups;
	};
	let visible_lobby_player_count = $state(LOBBY_VISIBLE_PLAYER_LIMIT);
	let visible_lobby_players = $derived(game_state.players.slice(0, visible_lobby_player_count));
	let grouped_visible_lobby_players = $derived(groupLobbyPlayersByZone(visible_lobby_players));
	let selected_lobby_player_key = $state<string | null>(null);
	let hidden_lobby_player_count = $derived(
		Math.max(game_state.players.length - visible_lobby_players.length, 0)
	);
	const togglePlayerMenu = (player: { username: string; zone?: string }) => {
		const key = participantKey(player.username, player.zone);
		selected_lobby_player_key = selected_lobby_player_key === key ? null : key;
	};
	const kickPlayer = (player: { username: string; zone?: string }) => {
		socket_game_controls.kick_player(player);
		selected_lobby_player_key = null;
	};

	if (cqc_code === 'null') {
		cqc_code = null;
	}
</script>

<div class="w-full h-full text-cq-text">
	<div class="grid grid-cols-3 pt-12">
		<!--mt-12 -->
		<div class="flex justify-center">
			<p class="m-auto text-2xl">
				{$t('play_page.join_description', {
					url:
						window.location.host === 'classquiz.de'
							? 'cquiz.de'
							: `${window.location.host}/play`,
					pin: game_pin
				})}
			</p>
		</div>
		<img
			onclick={() => (fullscreen_open = true)}
			alt={$t('play_page.join_qr_alt')}
			src="/api/v1/utils/qr/{game_pin}"
			class="cq-card block mx-auto w-1/2 bg-white p-2 hover:cursor-pointer dark:bg-white"
		/>
		{#if cqc_code}
			<div class="m-auto">
				<div class="flex justify-center my-4">
					<p class="m-auto text-2xl">
						{#if game_state.players.length <= 1}
							{$t('play_page.players_waiting', {
								count: game_state.players.length ?? 0
							})}
						{:else}
							{$t('play_page.players_waiting_plural', {
								count: game_state.players.length ?? 0
							})}
						{/if}
					</p>
				</div>
				<div class="flex-col flex justify-center">
					<p class="mx-auto">{$t('play_page.join_by_entering_code')}</p>
					<ControllerCodeDisplay code={cqc_code} />
				</div>
			</div>
		{:else}
			<div class="flex justify-center">
				<p class="m-auto text-2xl">
					{#if game_state.players.length <= 1}
						{$t('play_page.players_waiting', {
							count: game_state.players.length ?? 0
						})}
					{:else}
						{$t('play_page.players_waiting_plural', {
							count: game_state.players.length ?? 0
						})}
					{/if}
				</p>
			</div>
		{/if}
	</div>
	<p class="text-3xl text-center">
		{$t('words.pin')}: <span class="select-all">{game_pin}</span>
	</p>
	<div class="flex justify-center w-full mt-4">
		<div>
			<GrayButton
				disabled={game_state.players.length < 1}
				onclick={() => {
					socket_game_controls.start_game();
				}}
				>{$t('admin_page.start_game')}
			</GrayButton>
		</div>
	</div>
	<div class="cq-card w-full mt-4 p-2">
		<div class="grid grid-cols-[repeat(auto-fit,minmax(7rem,1fr))] gap-x-3 gap-y-2">
			{#each grouped_visible_lobby_players as group (group.key)}
				<div class="cq-surface-muted flex flex-col gap-1 px-3 py-2">
					<h2 class="text-sm font-semibold text-cq-text">{group.zone}</h2>
					<div class="flex min-h-6 flex-col gap-1">
						{#each group.players as player (participantKey(player.username, player.zone))}
							{@const player_key = participantKey(player.username, player.zone)}
							<div class="relative">
								<button
									type="button"
									class="link-hover text-left text-sm"
									aria-haspopup="menu"
									aria-expanded={selected_lobby_player_key === player_key}
									onclick={() => {
										togglePlayerMenu(player);
									}}>{player.username}</button
								>
								{#if selected_lobby_player_key === player_key}
									<div class="cq-card absolute left-0 top-full z-10 mt-1 w-max p-1" role="menu">
										<button
											type="button"
											role="menuitem"
											class="action-button w-full text-sm"
											aria-label="{$t('words.kick')} {formatPlayerName(player)}"
											onclick={() => {
												kickPlayer(player);
											}}
										>
											{$t('words.kick')}
										</button>
									</div>
								{/if}
							</div>
						{/each}
					</div>
				</div>
			{/each}
		</div>
		{#if hidden_lobby_player_count > 0}
			<button
				type="button"
				class="cq-surface-muted mt-2 w-fit p-2 text-lg font-semibold text-cq-muted hover:text-cq-text transition"
				onclick={() => (visible_lobby_player_count += LOBBY_VISIBLE_PLAYER_LIMIT)}
			>
				+{Math.min(LOBBY_VISIBLE_PLAYER_LIMIT, hidden_lobby_player_count)}
			</button>
		{/if}
	</div>
</div>

{#if fullscreen_open}
	<div
		class="fixed top-0 left-0 z-50 w-screen h-screen bg-cq-text/50 flex p-2"
		transition:fade|global={{ duration: 80 }}
		onclick={() => (fullscreen_open = false)}
		tabindex="0"
		role="button"
		aria-label={$t('words.close')}
		onkeydown={(e) =>
			e.key === 'Enter' || e.key === ' '
				? () => {
						fullscreen_open = false;
					}
				: null}
	>
		<img
			alt={$t('play_page.join_qr_alt')}
			src="/api/v1/utils/qr/{game_pin}"
			class="cq-card object-contain m-auto h-full bg-white p-2"
		/>
	</div>
{/if}
