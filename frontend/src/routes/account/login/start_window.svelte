<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import { getLocalization } from '$lib/i18n';
	import OAuthBlock from './oauth_block.svelte';

	type LoginMethod = 'PASSWORD' | 'PASSKEY' | 'BACKUP' | 'TOTP';

	interface LoginSessionData {
		session_id: string;
		step_1: LoginMethod[];
		step_2: LoginMethod[];
	}

	interface Props {
		session_data: LoginSessionData;
		step: number;
	}

	let {
		session_data = $bindable({ session_id: '', step_1: [], step_2: [] }),
		step = $bindable()
	}: Props = $props();

	const { t } = getLocalization();
	let email = $state('');
	let emailEmpty = $derived(email === '');
	let isSubmitting = $state(false);

	const start_login = async (e: Event): Promise<void> => {
		e.preventDefault();
		if (emailEmpty) {
			return;
		}
		isSubmitting = true;

		const res = await fetch('/api/v1/login/start', {
			method: 'post',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({ email: email })
		});
		session_data = await res.json();
		step = 1;
	};
</script>

<div class="px-6 py-5">
	<h2 class="text-3xl font-bold text-center text-cq-text">ClassQuiz</h2>

	<h3 class="mt-1 text-xl font-medium text-center text-cq-text">
		{$t('login_page.welcome_back')}
	</h3>

	<p class="mt-1 text-center text-cq-muted">
		{$t('login_page.login_or_create_account')}
	</p>

	<form onsubmit={start_login}>
		<div class="w-full mt-4">
			<div class="cq-surface-muted p-4">
				<div class="relative bg-inherit w-full">
					<input
						id="email"
						bind:value={email}
						name="email"
						type="text"
						class="w-full peer bg-transparent h-10 rounded-lg text-cq-text placeholder-transparent ring-2 px-2 ring-cq-border focus:ring-cq-brand focus:outline-hidden"
						placeholder={$t('login_page.email_or_username')}
						autocomplete="email"
					/>
					<label
						for="email"
						class="absolute cursor-text left-0 -top-3 text-sm text-cq-text bg-inherit mx-1 px-1 peer-placeholder-shown:text-base peer-placeholder-shown:text-cq-muted peer-placeholder-shown:top-2 peer-focus:-top-3 peer-focus:text-cq-text peer-focus:text-sm transition-all"
					>
						{$t('login_page.email_or_username')}
					</label>
				</div>
			</div>
			<div class="flex items-center justify-between mt-4 gap-3">
				<a href="/account/reset-password" class="text-sm text-cq-muted link-hover"
					>{$t('register_page.forgot_password?')}</a
				>

				<button class="accent-button w-fit" disabled={emailEmpty} type="submit">
					{#if isSubmitting}
						<svg class="h-4 w-4 animate-spin mx-auto" viewBox="3 3 18 18">
							<path
								class="fill-cq-text"
								d="M12 5C8.13401 5 5 8.13401 5 12C5 15.866 8.13401 19 12 19C15.866 19 19 15.866 19 12C19 8.13401 15.866 5 12 5ZM3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12Z"
							/>
							<path
								class="fill-[var(--cq-surface-muted)]"
								d="M16.9497 7.05015C14.2161 4.31648 9.78392 4.31648 7.05025 7.05015C6.65973 7.44067 6.02656 7.44067 5.63604 7.05015C5.24551 6.65962 5.24551 6.02646 5.63604 5.63593C9.15076 2.12121 14.8492 2.12121 18.364 5.63593C18.7545 6.02646 18.7545 6.65962 18.364 7.05015C17.9734 7.44067 17.3403 7.44067 16.9497 7.05015Z"
							/>
						</svg>
					{:else}
						{$t('words.continue')}
					{/if}
				</button>
			</div>
			<OAuthBlock />
		</div>
	</form>
</div>

<div
	class="cq-surface-muted flex items-center justify-center py-4 text-center rounded-none border-x-0 border-b-0"
>
	<span class="text-sm text-cq-muted">{$t('login_page.already_have_account')} </span>

	<a href="/account/register" class="mx-2 text-sm font-bold text-cq-text link-hover"
		>{$t('words.register')}</a
	>
</div>
