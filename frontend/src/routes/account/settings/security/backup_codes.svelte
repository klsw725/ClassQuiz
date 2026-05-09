<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import { getLocalization } from '$lib/i18n';

	const { t } = getLocalization();
	let { backup_code = $bindable() } = $props();

	let already_downloaded = false;

	const download_code = (force = false) => {
		if (already_downloaded && !force) {
			return;
		}
		const el = document.createElement('a');
		el.setAttribute('href', `data:text/plain;charset=utf-8,${backup_code}`);
		el.setAttribute('download', 'ClassQuiz-Backup-Code.txt');
		el.style.display = 'none';
		document.body.appendChild(el);
		el.click();
		document.body.removeChild(el);
		already_downloaded = true;
	};
</script>

<div
	class="fixed top-0 left-0 z-30 h-screen w-screen bg-black/45 p-4 backdrop-blur-sm md:p-12 xl:p-24"
>
	<div class="mx-auto h-full w-full max-w-4xl">
		<button
			class="action-button w-fit rounded-b-none"
			onclick={() => {
				backup_code = undefined;
			}}
			>{$t('words.close')}
		</button>
		<div
			class="cq-card flex h-[calc(100%-2.5rem)] w-full flex-col gap-6 overflow-y-auto rounded-tl-none p-6 text-center"
		>
			<h2 class="m-auto text-3xl font-semibold text-cq-text">
				{$t('security_settings.backup_codes.your_backup_code')}
			</h2>
			<button
				type="button"
				class="cq-surface-muted m-auto select-all break-all p-4 font-mono text-xl text-cq-text"
				onclick={() => {
					download_code(false);
				}}
			>
				{backup_code}
			</button>
			<p class="m-auto text-cq-muted">
				{$t('security_settings.backup_codes.save_somewhere_save')}
			</p>
			<button
				onclick={() => {
					download_code(true);
				}}
				class="accent-button m-auto w-fit"
				>{$t('security_settings.backup_codes.download_code')}
			</button>
		</div>
	</div>
</div>
