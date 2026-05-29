<!--
SPDX-FileCopyrightText: 2026 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import QRCode from 'qrcode';
	import { browser } from '$app/environment';
	import BrownButton from '$lib/components/buttons/brown.svelte';
	import GrayButton from '$lib/components/buttons/gray.svelte';
	import type { PageData } from './$types';

	interface Props {
		data: PageData;
	}

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
			copy_status = '복사되었습니다';
		} catch {
			copy_status = copy_with_textarea(player_url) ? '복사되었습니다' : '복사에 실패했습니다';
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
	<title>ClassQuiz - 솔로 호스트</title>
</svelte:head>

<main class="flex min-h-screen items-center justify-center px-4 py-10 text-cq-text">
	<section class="cq-card flex w-full max-w-2xl flex-col gap-5 p-6 text-center">
		<div>
			<p class="text-sm font-semibold uppercase tracking-wide text-cq-muted">솔로 미리보기</p>
			<h1 class="mt-2 text-3xl font-bold text-cq-text">이 솔로 게임 공유</h1>
		</div>

		<p class="text-cq-muted">플레이어 링크를 복사해서 참가자에게 보내세요.</p>

		{#if player_url}
			<div class="cq-surface-muted flex flex-col gap-3 p-3 text-left">
				{#if qr_image_url}
					<img
						src={qr_image_url}
						alt="솔로 플레이어 링크 QR 코드"
						class="cq-surface mx-auto aspect-square w-full max-w-56 bg-white p-2 dark:bg-white"
					/>
				{/if}
				<div>
					<p class="text-sm font-semibold text-cq-text">플레이어 링크</p>
					<p class="break-all text-sm text-cq-muted">{player_url}</p>
				</div>
				<BrownButton onclick={copy_player_url}>플레이어 링크 복사</BrownButton>
				{#if copy_status}
					<p class="text-center text-sm text-cq-muted" role="status">{copy_status}</p>
				{/if}
			</div>
		{:else}
			<p class="cq-surface-muted p-3 text-cq-muted" role="alert">
				사용 가능한 솔로 플레이어 링크가 없습니다.
			</p>
		{/if}

		<GrayButton href="/dashboard">대시보드로 돌아가기</GrayButton>
	</section>
</main>
