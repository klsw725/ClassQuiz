<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import { browser } from '$app/environment';
	import { fade } from 'svelte/transition';
	import { thumbHashToDataURL } from 'thumbhash';

	interface Props {
		src: string;
		css_classes?: string;
		added_thumbhash_classes?: string;
		muted?: boolean;
		allow_fullscreen?: boolean;
	}

	let {
		src = $bindable(),
		css_classes = 'max-h-64 h-auto w-auto',
		added_thumbhash_classes = 'h-full',
		muted = true,
		allow_fullscreen = true
	}: Props = $props();
	let type: 'img' | 'video' | 'audio' | 'youtube' | undefined = $state(undefined);
	const youtube_marker_pattern = /^youtube:([A-Za-z0-9_-]{11})$/;
	const youtube_video_id = $derived(src.match(youtube_marker_pattern)?.[1]);
	const youtube_embed_src = $derived(
		youtube_video_id ? `https://www.youtube.com/embed/${youtube_video_id}` : undefined
	);

	interface ImageData {
		data: string;
		alt_text?: string;
	}

	let img_data = $state<ImageData>();
	let video_el = $state<HTMLVideoElement>();
	let thumbhash_data: string = $state();

	function base64ToBytes(base64: string): Uint8Array {
		const binString = atob(base64);
		return Uint8Array.from(binString, (m) => m.codePointAt(0));
	}

	const get_media = async (_: string): Promise<void> => {
		if (youtube_video_id) {
			type = 'youtube';
			return;
		}
		if (!browser) {
			return;
		}
		const res = await fetch(`/api/v1/storage/info/${src}`);
		const fileType = res.headers.get('Content-Type');
		if (fileType?.includes('video')) {
			type = 'video';
		} else if (fileType?.includes('audio')) {
			type = 'audio';
		} else {
			type = 'img';
			thumbhash_data = thumbHashToDataURL(
				base64ToBytes(res.headers.get('x-thumbhash') ?? '')
			);
			const data = await fetch(`/api/v1/storage/download/${src}`);
			img_data = {
				data: URL.createObjectURL(await data.blob()),
				alt_text: new TextDecoder().decode(
					base64ToBytes(res.headers.get('X-Alt-Text') ?? '')
				)
			};
			thumbhash_data = undefined;
		}
	};
	let media = $derived(get_media(src));

	let fullscreen_open = $state(false);

	const open_fullscreen = () => {
		if (!allow_fullscreen) {
			return;
		}
		fullscreen_open = true;
	};

	$effect(() => {
		video_el?.setAttribute('x-webkit-airplay', 'deny');
	});
</script>

{#await media}
	<img src={thumbhash_data} class={`${css_classes} ${added_thumbhash_classes}`} />
{:then _}
	{#if type === 'img' && img_data}
		<img
			in:fade|global={{ duration: 300 }}
			src={img_data.data}
			alt={img_data.alt_text ?? '사용할 수 없음'}
			class={css_classes}
			onclick={() => open_fullscreen()}
		/>
	{:else if type === 'video'}
		<video
			bind:this={video_el}
			class={css_classes}
			disablepictureinpicture
			controls
			autoplay
			loop
			{muted}
			preload="metadata"
		>
			<source src="/api/v1/storage/download/{src}" />
		</video>
	{:else if type === 'audio'}
		<audio class={css_classes} controls preload="metadata">
			<source src="/api/v1/storage/download/{src}" />
		</audio>
	{:else if type === 'youtube' && youtube_video_id && youtube_embed_src}
		{#if allow_fullscreen}
			<iframe
				src={youtube_embed_src}
				title="YouTube 동영상 플레이어"
				class={`aspect-video min-h-[200px] min-w-[200px] ${css_classes}`}
				allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
				allowfullscreen
				loading="lazy"
				referrerpolicy="strict-origin-when-cross-origin"
			></iframe>
		{:else}
			<div
				class={`cq-surface-muted flex items-center justify-center text-cq-muted ${css_classes}`}
				aria-label="YouTube 동영상"
			>
				YouTube
			</div>
		{/if}
	{:else}
		<p>알 수 없는 미디어 유형입니다</p>
	{/if}
{/await}

{#if fullscreen_open && img_data}
	<div
		class="fixed top-0 left-0 z-50 w-screen h-screen bg-cq-text/50 fle p-2"
		transition:fade|global={{ duration: 80 }}
		onclick={() => (fullscreen_open = false)}
	>
		<img
			src={img_data.data}
			alt={img_data.alt_text ?? '사용할 수 없음'}
			class="object-cover rounded-lg m-auto max-h-full max-w-full"
		/>
	</div>
{/if}
