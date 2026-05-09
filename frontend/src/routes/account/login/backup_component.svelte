<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import { getLocalization } from '$lib/i18n';

	const { t } = getLocalization();
	let {
		session_data,
		selected_method = $bindable(),
		done = $bindable(),
		step = $bindable()
	} = $props();

	let backup_code = $state('');
	let isSubmitting = $state(false);

	let backup_code_valid = $derived(backup_code.length === 64);

	const continue_in_login = async (e: Event) => {
		e.preventDefault();
		if (!backup_code_valid) {
			return;
		}
		isSubmitting = true;
		const res = await fetch(`/api/v1/login/step/1?session_id=${session_data.session_id}`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({ auth_type: 'BACKUP', data: backup_code })
		});
		if (res.status === 200) {
			window.location.reload();
			done = true;
		} else {
			step += 1;
			selected_method = null;
		}
	};
</script>

<div class="px-6 py-5">
	<h2 class="text-3xl font-bold text-center text-cq-text">ClassQuiz</h2>

	<form onsubmit={continue_in_login}>
		<div class="w-full mt-4">
			<div class="cq-surface-muted p-4">
				<div class="relative bg-inherit w-full">
					<input
						id="backup_code"
						bind:value={backup_code}
						name="backup_code"
						type="text"
						class="w-full peer bg-transparent h-10 rounded-lg text-cq-text placeholder-transparent ring-2 px-2 ring-cq-border focus:ring-cq-brand focus:outline-hidden"
						placeholder={$t('words.backup_code')}
					/>
					<label
						for="backup_code"
						class="absolute cursor-text left-0 -top-3 text-sm text-cq-text bg-inherit mx-1 px-1 peer-placeholder-shown:text-base peer-placeholder-shown:text-cq-muted peer-placeholder-shown:top-2 peer-focus:-top-3 peer-focus:text-cq-text peer-focus:text-sm transition-all"
					>
						{$t('words.backup_code')}
					</label>
				</div>
			</div>
			<div class="flex items-center justify-between mt-4 gap-3">
				<button
					onclick={() => {
						selected_method = 'BACKUP';
					}}
					class="text-sm text-cq-muted link-hover"
					>{$t('login_page.use_backup_code')}</button
				>
				<button class="accent-button w-fit" disabled={!backup_code_valid} type="submit">
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
		</div>
	</form>
</div>
