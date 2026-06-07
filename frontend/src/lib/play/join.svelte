<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import { socket } from '$lib/socket';
	import { onDestroy, onMount } from 'svelte';
	import { browser } from '$app/environment';
	import * as Sentry from '@sentry/browser';
	import { getLocalization } from '$lib/i18n';
	import BrownButton from '$lib/components/buttons/brown.svelte';

	const { t } = getLocalization();

	interface Props {
		game_pin: string;
		game_mode: unknown;
		username: string;
		zone?: string;
	}

	let {
		game_pin = $bindable(),
		game_mode = $bindable(),
		username = $bindable(),
		zone = $bindable('1구역')
	}: Props = $props();
	let custom_field = $state();
	let custom_field_value = $state();
	let captcha_enabled = $state();
	const zones = Array.from({ length: 11 }, (_, index) => `${index + 1}구역`);

	let hcaptchaSitekey = import.meta.env.VITE_HCAPTCHA;

	let hcaptcha = {
		execute: async (_a, _b) => ({ response: '' }), // eslint-disable-line @typescript-eslint/no-unused-vars
		// eslint-disable-next-line @typescript-eslint/no-empty-function
		render: (_a, _b) => {} // eslint-disable-line @typescript-eslint/no-unused-vars
	};
	let hcaptchaWidgetID: unknown;

	onMount(() => {
		if (browser) {
			prefetch_username();
			hcaptcha = window.hcaptcha;
			if (hcaptcha.render) {
				hcaptchaWidgetID = hcaptcha.render('hcaptcha', {
					sitekey: hcaptchaSitekey,
					size: 'invisible',
					theme: 'dark'
				});
			}
		}
	});

	onDestroy(() => {
		if (browser) {
			hcaptcha = {
				execute: async () => ({ response: '' }),
				// eslint-disable-next-line @typescript-eslint/no-empty-function
				render: () => {}
			};
		}
	});

	const prefetch_username = async () => {
		const res = await fetch('/api/v1/users/me');
		if (res.status !== 200) {
			return;
		}
		const json = await res.json();
		username = json.username;
	};

	const set_game_pin = async () => {
		let process_var: { env: { API_URL?: string } };
		try {
			process_var = { env: { API_URL: process.env.API_URL } };
		} catch {
			process_var = { env: { API_URL: undefined } };
		}

		const res = await fetch(
			`${process_var.env.API_URL ?? ''}/api/v1/quiz/play/check_captcha/${game_pin}`
		);
		const json = await res.json();
		game_mode = json.game_mode;
		if (res.status === 200) {
			captcha_enabled = json.enabled;
			custom_field = json.custom_field;
		}
		if (res.status === 404) {
			/*			alertModal.set({
                open: true,
                title: 'Game not found',
                body: 'The game pin you entered seems invalid.'
            });*/
			if (browser) {
				alert($t('admin_page.game_not_found'));
			}
			game_pin = '';
			return;
		}
		if (res.status !== 200) {
			/*			alertModal.set({
                open: true,
                body: `Unknown error with response-code ${res.status}`,
                title: 'Unknown Error'
            });*/
			alert($t('admin_page.error'));
			return;
		}
	};

	$effect(() => {
		if (game_pin.length > 5) {
			set_game_pin();
		}
	});

	const setUsername = async (e: Event) => {
		e.preventDefault();
		if (username.length < 2) {
			return;
		}
		let captcha_resp: string;
		if (captcha_enabled) {
			if (hcaptchaSitekey) {
				try {
					const { response } = await hcaptcha.execute(hcaptchaWidgetID, {
						async: true
					});
					captcha_resp = response;
					socket.emit('join_game', {
						username: username,
						game_pin: game_pin,
						zone: zone,
						captcha: captcha_resp,
						custom_field: custom_field ? custom_field_value : undefined
					});
				} catch (e) {
					if (import.meta.env.VITE_SENTRY !== null) {
						Sentry.captureException(e);
					}
					/*					alertModal.set({
                        open: true,
                        body: "The captcha failed, which is normal, but most of the time it's fixed by reloading!",
                        title: 'Captcha failed'
                    });*/
					alert($t('play_page.captcha_failed'));
					window.location.reload();
				}
			} else if (import.meta.env.VITE_RECAPTCHA) {
				// eslint-disable-next-line no-undef
				grecaptcha.ready(() => {
					// eslint-disable-next-line no-undef
					grecaptcha
						.execute(import.meta.env.VITE_RECAPTCHA, { action: 'submit' })
						.then(function (token) {
							socket.emit('join_game', {
								username: username,
								game_pin: game_pin,
								zone: zone,
								captcha: token,
								custom_field: custom_field ? custom_field_value : undefined
							});
						});
				});
			}
		} else {
			socket.emit('join_game', {
				username: username,
				game_pin: game_pin,
				zone: zone,
				captcha: undefined,
				custom_field: custom_field ? custom_field_value : undefined
			});
		}
	};
	socket.on('game_not_found', () => {
		game_pin = '';
		if (browser) {
			alert($t('admin_page.game_not_found'));
		}
	});
	$effect(() => {
		const cleaned = game_pin.replace(/\D/g, '');
		if (game_pin.replace(/\D/g, '') === game_pin) {
			return;
		}
		game_pin = cleaned;
	});
</script>

<svelte:head>
	{#if captcha_enabled && hcaptchaSitekey}
		<script src="https://js.hcaptcha.com/1/api.js" async defer></script>
	{/if}
	{#if import.meta.env.VITE_RECAPTCHA && captcha_enabled}
		<script
			src="https://www.google.com/recaptcha/api.js?render={import.meta.env.VITE_RECAPTCHA}"
		></script>
	{/if}
</svelte:head>

{#if game_pin === '' || game_pin.length < 6}
	<div class="flex min-h-screen w-screen items-center justify-center px-4 text-cq-text">
		<form class="cq-card flex w-full max-w-md flex-col gap-4 p-6 text-center">
			<h1 class="text-lg font-semibold text-cq-text">{$t('words.game_pin')}</h1>
			<input
				class="cq-surface-muted w-full self-center rounded-lg p-3 text-center text-2xl tracking-widest text-cq-text outline-hidden ring-2 ring-cq-border transition-all focus:ring-cq-brand"
				bind:value={game_pin}
				maxlength="6"
				inputmode="numeric"
			/>
			<!--				use:tippy={{content: "Please enter the game pin", sticky: true, placement: 'top'}}-->

			<div class="mt-2">
				<BrownButton disabled={game_pin.length < 6}>{$t('words.submit')}</BrownButton>
			</div>
		</form>
	</div>
{:else}
	<div class="flex min-h-screen w-screen items-center justify-center px-4 text-cq-text">
		<form
			onsubmit={setUsername}
			class="cq-card flex w-full max-w-md flex-col gap-4 p-6 text-center"
		>
			<h1 class="text-lg font-semibold text-cq-text">{$t('words.username')}</h1>
			<input
				class="cq-surface-muted w-full self-center rounded-lg p-3 text-center text-cq-text outline-hidden ring-2 ring-cq-border transition-all focus:ring-cq-brand"
				bind:value={username}
				maxlength="17"
			/>
			<h1 class="text-lg font-semibold text-cq-text">{$t('words.zone')}</h1>
			<select
				class="cq-surface-muted w-full self-center rounded-lg p-3 text-center text-cq-text outline-hidden ring-2 ring-cq-border transition-all focus:ring-cq-brand"
				bind:value={zone}
			>
				{#each zones as zone_option (zone_option)}
					<option value={zone_option}>{zone_option}</option>
				{/each}
			</select>
			{#if custom_field}
				<h1 class="text-lg font-semibold text-cq-text">{custom_field}</h1>
				<input
					class="cq-surface-muted w-full self-center rounded-lg p-3 text-center text-cq-text outline-hidden ring-2 ring-cq-border transition-all focus:ring-cq-brand"
					bind:value={custom_field_value}
				/>
			{/if}

			<div class="mt-2">
				<BrownButton disabled={username.length < 2} onclick={setUsername}
					>{$t('words.submit')}</BrownButton
				>
			</div>
		</form>
	</div>
{/if}
<div
	id="hcaptcha"
	class="h-captcha"
	data-sitekey={hcaptchaSitekey}
	data-size="invisible"
	data-theme="dark"
></div>
