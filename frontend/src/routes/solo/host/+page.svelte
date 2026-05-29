<!--
SPDX-FileCopyrightText: 2026 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import QRCode from 'qrcode';
	import { browser } from '$app/environment';
	import BrownButton from '$lib/components/buttons/brown.svelte';
	import GrayButton from '$lib/components/buttons/gray.svelte';
	import { getLocalization } from '$lib/i18n';
	import type { PageData } from './$types';

	interface Props {
		data: PageData;
	}

	const { t } = getLocalization();

	let { data }: Props = $props();
	let copy_status = $state('');
	let qr_image_url = $state('');

	let player_url = $derived.by(() => {
		if (!data.pin || !data.token) {
			return '';
		}
		const params = new URLSearchParams({ pin: data.pin, token: data.token });
		if (!browser) {
			return `/solo?${params.toString()}`;
		}
		return `${window.location.origin}/solo?${params.toString()}`;
	});

	const copy_with_textarea = (text: string) => {
		const textarea = document.createElement('textarea');
		textarea.value = text;
		textarea.setAttribute('readonly', '');
		textarea.style.position = 'absolute';
		textarea.style.left = '-9999px';

		const selection = document.getSelection();
		const selected_range =
			selection && selection.rangeCount > 0 ? selection.getRangeAt(0) : undefined;

		document.body.appendChild(textarea);
		textarea.select();

		try {
			return document.execCommand('copy');
		} catch {
			return false;
		} finally {
			document.body.removeChild(textarea);
			if (selection && selected_range) {
				selection.removeAllRanges();
				selection.addRange(selected_range);
			}
		}
	};

	const copy_player_url = async () => {
		if (!player_url || !browser) {
			return;
		}
		try {
			await navigator.clipboard.writeText(player_url);
			copy_status = $t('components.popover.copied_to_clipboard');
		} catch {
			copy_status = copy_with_textarea(player_url)
				? $t('components.popover.copied_to_clipboard')
				: $t('components.popover.copy_failed');
		}
	};

	$effect(() => {
		if (!browser || !player_url) {
			qr_image_url = '';
			return;
		}

		let cancelled = false;
		qr_image_url = '';
		QRCode.toDataURL(player_url)
			.then((data_url) => {
				if (!cancelled) {
					qr_image_url = data_url;
				}
			})
			.catch(() => {
				if (!cancelled) {
					qr_image_url = '';
				}
			});

		return () => {
			cancelled = true;
		};
	});
</script>

<svelte:head>
	<title>ClassQuiz - {$t('solo_page.host_meta.title')}</title>
</svelte:head>

<main class="flex min-h-screen items-center justify-center px-4 py-10 text-cq-text">
	<section class="cq-card flex w-full max-w-2xl flex-col gap-5 p-6 text-center">
		<div>
			<p class="text-sm font-semibold uppercase tracking-wide text-cq-muted">{$t('solo_page.preview')}</p>
			<h1 class="mt-2 text-3xl font-bold text-cq-text">{$t('solo_page.share_this_game')}</h1>
		</div>

		<p class="text-cq-muted">{$t('solo_page.copy_player_link_help')}</p>

		{#if player_url}
			<div class="cq-surface-muted flex flex-col gap-3 p-3 text-left">
				{#if qr_image_url}
					<img
						src={qr_image_url}
						alt={$t('solo_page.player_link_qr_alt')}
						class="cq-surface mx-auto aspect-square w-full max-w-56 bg-white p-2 dark:bg-white"
					/>
				{/if}
				<div>
					<p class="text-sm font-semibold text-cq-text">{$t('solo_page.player_link')}</p>
					<p class="break-all text-sm text-cq-muted">{player_url}</p>
				</div>
				<BrownButton onclick={copy_player_url}>{$t('solo_page.copy_player_link')}</BrownButton>
				{#if copy_status}
					<p class="text-center text-sm text-cq-muted" role="status">{copy_status}</p>
				{/if}
			</div>
		{:else}
			<p class="cq-surface-muted p-3 text-cq-muted" role="alert">
				{$t('solo_page.no_player_link')}
			</p>
		{/if}

		<GrayButton href="/dashboard">{$t('solo_page.back_to_dashboard')}</GrayButton>
	</section>
</main>
