<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import { getLocalization } from '$lib/i18n';
	import { DateTime } from 'luxon';
	import { UAParser } from 'ua-parser-js';
	import Spinner from '$lib/Spinner.svelte';
	import { onMount } from 'svelte';
	import BrownButton from '$lib/components/buttons/brown.svelte';

	const { t } = getLocalization();

	interface UserAccount {
		id: string;
		email: string;
		username: string;
		verified: boolean;
		created_at: string;
	}

	interface ChangePasswordData {
		oldPassword: string;
		newPassword: string;
		newPasswordConfirm: string;
	}

	interface ApiKey {
		key: string;
	}

	interface SessionData {
		id: string;
		created_at: string;
		last_seen: string;
		user_agent: string;
	}

	let changePasswordData: ChangePasswordData = $state({
		oldPassword: '',
		newPassword: '',
		newPasswordConfirm: ''
	});

	let this_session: SessionData | undefined = $state();

	let passwordChangeDataValid = $derived(
		changePasswordData.newPassword === changePasswordData.newPasswordConfirm &&
			changePasswordData.newPassword.length >= 8 &&
			changePasswordData.oldPassword !== changePasswordData.newPassword &&
			changePasswordData.oldPassword !== ''
	);

	const changePassword = async (e: Event) => {
		e.preventDefault();
		if (!passwordChangeDataValid) {
			return;
		}
		const res = await fetch('/api/v1/users/password/update', {
			method: 'PUT',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({
				old_password: changePasswordData.oldPassword,
				new_password: changePasswordData.newPassword
			})
		});
		if (res.status === 200) {
			alert('Password changed');
			window.location.assign('/account/login');
		} else {
			alert('Password change failed');
		}
	};

	const getUser = async (): Promise<UserAccount> => {
		const response = await fetch('/api/v1/users/me', {
			method: 'GET',
			headers: {
				'Content-Type': 'application/json'
			}
		});
		if (response.status === 200) {
			return await response.json();
		} else {
			window.location.assign('/account/login');
		}
	};

	onMount(() => {
		api_keys = get_api_keys();
	});

	const get_api_keys = async (): Promise<ApiKey[]> => {
		const res = await fetch('/api/v1/users/api_keys');
		const api_keys_temp: ApiKey[] = await res.json();
		console.log(api_keys_temp);
		return api_keys_temp;
	};

	let api_keys: Promise<ApiKey[]> | undefined = $state();

	const add_api_key = async () => {
		await fetch('/api/v1/users/api_keys', { method: 'POST' });
		api_keys = get_api_keys();
	};
	const formatDate = (date: string): string => {
		const dt = DateTime.fromISO(date);
		return dt.toLocaleString(DateTime.DATETIME_MED);
	};

	const delete_api_key = async (key: string) => {
		if (confirm('Do you really want to delete this API-Key?')) {
			await fetch(`/api/v1/users/api_keys?api_key=${key}`, { method: 'DELETE' });
			api_keys = get_api_keys();
		}
	};

	const getSessions = async (): Promise<SessionData[]> => {
		const res = await fetch('/api/v1/users/sessions/list');
		if (res.status === 200) {
			const res2 = await fetch('/api/v1/users/session');
			if (res2.status === 200) {
				this_session = await res2.json();
			}
			return await res.json();
		} else {
			window.location.assign('/account/login?returnTo=/account/settings');
		}
		return await res.json();
	};

	const getFormattedUserAgent = (userAgent: string): string => {
		const parser = new UAParser(userAgent);
		const result = parser.getResult();
		return `${result.browser.name} ${result.browser.version} (${result.os.name})`;
	};

	const deleteSession = async (session_id: string) => {
		const res = await fetch(`/api/v1/users/sessions/${session_id}`, {
			method: 'DELETE'
		});
		if (res.status === 200) {
			window.location.reload();
		}
	};
</script>

<svelte:head>
	<title>ClassQuiz - Settings</title>
</svelte:head>

{#await getUser()}
	<Spinner />
{:then user}
	<div class="px-4 py-8 text-cq-text">
		<div class="cq-card grid gap-6 p-5 lg:grid-cols-[auto_1fr]">
			<div class="flex flex-col items-center gap-3">
				<img
					class="cq-surface-muted w-40 rounded-md object-cover p-2 md:w-80"
					src="/api/v1/users/avatar"
					alt="Profile image of {user.username}"
				/>
				<div class="flex justify-center">
					<BrownButton href="/account/settings/avatar"
						>{$t('settings_page.change_avatar')}</BrownButton
					>
				</div>
			</div>
			<div class="grid gap-5">
				<div class="grid gap-4 md:grid-cols-[1fr_auto]">
					<div>
						<h1 class="my-2 text-4xl font-bold text-cq-text">{user.username}</h1>
						<p class="mb-6 text-lg text-cq-muted md:max-w-lg">
							{$t('words.email')}: {user.email}
						</p>
					</div>
					<div class="cq-surface-muted flex justify-center p-4">
						<div class="m-auto flex flex-col gap-2">
							<BrownButton href="/account/settings/security"
								>{$t('settings_page.security_settings')}
							</BrownButton>
							<BrownButton href="/account/controllers"
								>ClassQuizController</BrownButton
							>
							<BrownButton href="/user/{user.id}">Public profile page</BrownButton>
						</div>
					</div>
				</div>
				<div class="grid gap-4 xl:grid-cols-2">
					<form
						class="cq-surface-muted flex flex-col gap-3 p-4"
						onsubmit={changePassword}
					>
						<label class="flex flex-col gap-1 text-sm font-medium text-cq-text"
							>{$t('settings_page.old_password')}:<input
								type="password"
								class="cq-surface p-2 outline-hidden focus:ring-2 focus:ring-cq-brand"
								bind:value={changePasswordData.oldPassword}
							/></label
						>
						<label class="flex flex-col gap-1 text-sm font-medium text-cq-text"
							>{$t('settings_page.new_password')}:<input
								type="password"
								class="cq-surface p-2 outline-hidden focus:ring-2 focus:ring-cq-brand"
								bind:value={changePasswordData.newPassword}
							/></label
						>
						<label class="flex flex-col gap-1 text-sm font-medium text-cq-text"
							>{$t('settings_page.repeat_password')}:<input
								type="password"
								class="cq-surface p-2 outline-hidden focus:ring-2 focus:ring-cq-brand"
								bind:value={changePasswordData.newPasswordConfirm}
							/></label
						>
						<div class="mt-1 w-fit">
							<BrownButton disabled={!passwordChangeDataValid} type="submit">
								{$t('settings_page.change_password_submit')}
							</BrownButton>
						</div>
					</form>
					<div class="cq-surface-muted flex flex-col gap-3 p-4">
						<div class="w-fit">
							<BrownButton onclick={add_api_key}
								>{$t('settings_page.add_api_key')}</BrownButton
							>
						</div>
						{#await api_keys}
							<Spinner />
						{:then keys}
							{#each keys as key}
								<div
									class="cq-surface flex flex-col gap-2 p-3 text-sm md:flex-row md:items-center md:justify-between"
								>
									<span class="break-all font-mono text-cq-muted">{key.key}</span>
									<div class="inline-block">
										<BrownButton
											onclick={() => {
												delete_api_key(key.key);
											}}
											>{$t('words.delete')}
										</BrownButton>
									</div>
								</div>
							{/each}
						{/await}
					</div>
				</div>
			</div>
		</div>
	</div>
{/await}
{#await getSessions()}
	<Spinner />
{:then sessions}
	<div class="px-4 pb-8 text-cq-text">
		<div class="cq-card overflow-x-auto">
			<table class="min-w-full">
				<thead class="cq-surface-muted rounded-none border-x-0 border-t-0">
					<tr>
						<th
							scope="col"
							class="py-3 px-6 text-left text-xs font-medium tracking-wider text-cq-muted uppercase"
						>
							{$t('overview_page.created_at')}
						</th>
						<th
							scope="col"
							class="py-3 px-6 text-left text-xs font-medium tracking-wider text-cq-muted uppercase"
						>
							{$t('settings_page.last_seen')}
						</th>
						<th
							scope="col"
							class="py-3 px-6 text-left text-xs font-medium tracking-wider text-cq-muted uppercase"
						>
							{$t('words.browser')}
						</th>
						<th
							scope="col"
							class="py-3 px-6 text-left text-xs font-medium tracking-wider text-cq-muted uppercase"
						>
							{$t('settings_page.delete_this_session')}
						</th>
						<th
							scope="col"
							class="py-3 px-6 text-left text-xs font-medium tracking-wider text-cq-muted uppercase"
						>
							{$t('settings_page.this_session?')}
						</th>
					</tr>
				</thead>
				<tbody>
					{#each sessions as session}
						<tr class="border-b border-cq-border last:border-b-0">
							<td class="py-4 px-6 text-sm whitespace-nowrap text-cq-muted">
								{formatDate(session.created_at)}
							</td>
							<td class="py-4 px-6 text-sm whitespace-nowrap text-cq-muted">
								{formatDate(session.last_seen)}
							</td>
							<td class="py-4 px-6 text-sm whitespace-nowrap text-cq-muted">
								{getFormattedUserAgent(session.user_agent)}
							</td>
							<td class="py-4 px-6 text-sm whitespace-nowrap text-cq-muted">
								<button
									class="link-hover font-semibold text-cq-text underline decoration-cq-border underline-offset-4"
									onclick={() => {
										deleteSession(session.id);
									}}>{$t('words.delete')}</button
								>
							</td>
							<td class="py-4 px-6 text-sm whitespace-nowrap text-cq-muted">
								{#if session.id === this_session?.id}
									✅
								{:else}
									❌
								{/if}
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	</div>
{/await}
