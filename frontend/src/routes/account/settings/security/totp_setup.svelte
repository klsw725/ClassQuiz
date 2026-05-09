<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import QRCode from 'qrcode';
	import Spinner from '$lib/Spinner.svelte';
	import { getLocalization } from '$lib/i18n';

	const { t } = getLocalization();

	interface Props {
		totp_data: { url: string; secret: string } | undefined;
	}

	let { totp_data = $bindable() }: Props = $props();

	const get_image_url = async () => {
		return await QRCode.toDataURL(totp_data.url);
	};
</script>

<div
	class="fixed top-0 left-0 z-30 h-screen w-screen bg-black/45 p-4 backdrop-blur-sm md:p-12 xl:p-24"
>
	<div class="mx-auto h-full w-full max-w-6xl">
		<button
			class="action-button w-fit rounded-b-none"
			onclick={() => {
				totp_data = undefined;
			}}
			>{$t('words.close')}
		</button>
		<div class="cq-card h-[calc(100%-2.5rem)] w-full overflow-y-auto rounded-tl-none p-4">
			<div class="grid h-full w-full gap-4 lg:grid-cols-3">
				<div
					class="cq-surface-muted flex min-h-48 w-full flex-col justify-center gap-4 p-4 text-cq-muted"
				>
					<span class="m-auto"></span>
					<div class="flex">
						<p class="my-auto ml-auto text-right">
							{$t('security_settings.totp_setup.scan_to_set_up')}
						</p>
					</div>
					<div class="flex">
						<p class="my-auto ml-auto text-right">
							{$t('security_settings.totp_setup.enter_as_secret_if_no_see_code')}
						</p>
					</div>
				</div>
				<div class="flex min-h-80 w-full flex-col justify-start gap-3">
					<h2 class="m-auto text-2xl font-semibold text-cq-text">
						{$t('security_settings.totp_setup.totp_setup')}
					</h2>
					{#await get_image_url()}
						<Spinner my_20={false} />
					{:then data}
						<div class="cq-surface m-auto h-5/6 w-full object-contain p-3">
							<img
								src={data}
								alt="QR-Code for Totp-setup"
								class="w-full h-full object-contain"
							/>
						</div>
					{/await}
					<p
						class="cq-surface-muted m-auto select-all break-all p-2 font-mono text-cq-text"
					>
						{totp_data.secret}
					</p>
				</div>
				<div class="cq-surface-muted flex min-h-48 w-full justify-center p-4">
					<p class="m-auto text-3xl text-cq-text">
						{$t('security_settings.totp_setup.do_not_forget_backup_code')}
					</p>
				</div>
			</div>
		</div>
	</div>
</div>
