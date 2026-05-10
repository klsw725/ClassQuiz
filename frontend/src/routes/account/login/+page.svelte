<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import { alertModal } from '$lib/stores';
	import { navbarVisible } from '$lib/stores.svelte';
	import { slide } from 'svelte/transition';
	import Footer from '$lib/footer.svelte';
	import VerifiedBadge from './verified_badge.svelte';
	import StartWindow from './start_window.svelte';
	import SelectMethod from './select_method.svelte';
	import PasswordComponent from './password_component.svelte';
	import WebauthnComponent from './webauthn_component.svelte';
	import BackupComponent from './backup_component.svelte';
	import TotpComponent from './totp_component.svelte';
	import { browserSupportsWebAuthn } from '@simplewebauthn/browser';

	type LoginMethod = 'PASSWORD' | 'PASSKEY' | 'BACKUP' | 'TOTP';

	interface LoginSessionData {
		session_id: string;
		step_1: LoginMethod[];
		step_2: LoginMethod[];
		webauthn_data?: string;
	}

	navbarVisible.visible = true;

	let { data } = $props();
	let { verified } = data;

	let session_data = $state<LoginSessionData>({
		session_id: '',
		step_1: [],
		step_2: []
	});
	let step = $state(0);
	let selected_method = $state<LoginMethod | null>(null);
	let done = $state(false);

	const redirect_back = (done_var: boolean) => {
		if (done_var) {
			setTimeout(() => {
				window.location.reload();
			}, 100);
		}
	};
	let alertModalOpen = false;
	$effect(() => {
		redirect_back(done);
	});

	alertModal.subscribe((data) => {
		if (!alertModalOpen && data.open) {
			alertModalOpen = true;
		}
		if (alertModalOpen && !data.open) {
			window.location.reload();
		}
	});

	const check_auto = (stp: number) => {
		const update_step = (methods: LoginMethod[]) => {
			if (browserSupportsWebAuthn()) {
				return methods;
			}

			const filtered_methods = methods.filter((method) => method !== 'PASSKEY');
			if (filtered_methods.length === methods.length) {
				return methods;
			}

			return filtered_methods;
		};

		if (stp === 1) {
			const next_step_1 = update_step(session_data.step_1);
			if (next_step_1 !== session_data.step_1) {
				session_data.step_1 = next_step_1;
			}
			if (session_data.step_1.length === 1) {
				selected_method = session_data.step_1[0];
			}
		}
		if (stp === 2) {
			const next_step_2 = update_step(session_data.step_2);
			if (next_step_2 !== session_data.step_2) {
				session_data.step_2 = next_step_2;
			}
			if (session_data.step_2.length === 1) {
				selected_method = session_data.step_2[0];
			}
		}
	};
	$effect(() => check_auto(step));
</script>

<svelte:head>
	<title>ClassQuiz - Login</title>
</svelte:head>
<div class="flex min-h-screen items-center justify-center px-4 py-10 text-cq-text">
	{#if verified}
		<VerifiedBadge />
	{/if}

	<div class="cq-card w-full max-w-sm mx-auto overflow-hidden">
		{#if step === 0}
			<!--			<p>StartWindow</p>-->
			<div transition:slide|global>
				<StartWindow bind:session_data bind:step />
			</div>
		{:else if selected_method === null}
			<!--			<p>SelectWindow</p>-->
			<div transition:slide|global>
				<SelectMethod {session_data} {step} bind:selected_method />
			</div>
		{:else if selected_method === 'PASSWORD'}
			<!--			<p>PasswordWindow</p>-->
			<div transition:slide|global>
				<PasswordComponent {session_data} bind:done bind:step bind:selected_method />
			</div>
		{:else if selected_method === 'PASSKEY'}
			<!--			<p>WebauthnWindow</p>-->
			<div transition:slide|global>
				<WebauthnComponent {session_data} bind:done bind:step bind:selected_method />
			</div>
		{:else if selected_method === 'BACKUP'}
			<!--			<p>BackupWindow</p>-->
			<div transition:slide|global>
				<BackupComponent {session_data} bind:done bind:step bind:selected_method />
			</div>
		{:else if selected_method === 'TOTP'}
			<!--			<p>TotpWindow</p>-->
			<div transition:slide|global>
				<TotpComponent {session_data} bind:done bind:step bind:selected_method />
			</div>
		{/if}
	</div>
</div>
<Footer />
