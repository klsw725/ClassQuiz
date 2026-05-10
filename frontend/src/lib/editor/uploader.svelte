<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->
<script lang="ts">
	import { Dashboard as SvelteDashboard } from '@uppy/svelte';
	import Uppy from '@uppy/core';
	import DropTarget from '@uppy/drop-target';
	import XHRUpload from '@uppy/xhr-upload';
	import ImageEditor from '@uppy/image-editor';
	import Compressor from '@uppy/compressor';
	import { fade } from 'svelte/transition';
	import BrownButton from '$lib/components/buttons/brown.svelte';

	// CSS imports
	import '@uppy/core/dist/style.css';
	import '@uppy/dashboard/dist/style.css';
	import '@uppy/drop-target/dist/style.css';
	import '@uppy/image-editor/dist/style.css';
	import type { EditorData } from '../quiz_types';
	import { getLocalization } from '$lib/i18n';
	import { onMount } from 'svelte';
	import Library from '$lib/editor/uploader/Library.svelte';
	import Pixabay from '$lib/editor/uploader/Pixabay.svelte';

	const { t } = getLocalization();
	let {
		modalOpen = $bindable(),
		data = $bindable(),
		selected_question = $bindable(),
		video_upload = false,
		library_enabled = true,
		edit_id = $bindable()
	}: {
		modalOpen: boolean;
		data: EditorData;
		selected_question?: number;
		video_upload: boolean;
		library_enabled?: boolean;
		edit_id?: string;
	} = $props();

	// eslint-disable-next-line no-undef
	let video_popup: undefined | WindowProxy = $state(undefined);

	let selected_type: AvailableUploadTypes | null = $state(null);

	// eslint-disable-next-line no-unused-vars
	enum AvailableUploadTypes {
		// eslint-disable-next-line no-unused-vars
		Image,
		// eslint-disable-next-line no-unused-vars
		Video,
		// eslint-disable-next-line no-unused-vars
		Audio,
		// eslint-disable-next-line no-unused-vars
		Library,
		// eslint-disable-next-line no-unused-vars
		Pixabay,
		// eslint-disable-next-line no-unused-vars
		YouTube
	}

	const image_restrictions = {
		maxFileSize: 10_490_000,
		maxNumberOfFiles: 1,
		allowedFileTypes: ['image/*']
	};
	const audio_restrictions = {
		maxFileSize: 10_490_000,
		maxNumberOfFiles: 1,
		allowedFileTypes: ['audio/mpeg']
	};

	const uppy = new Uppy()
		.use(DropTarget, {
			target: document.body
		})
		.use(ImageEditor, {
			quality: 0.8
		})
		.use(Compressor, {
			quality: 0.6
		})
		.use(XHRUpload, {
			endpoint: `/api/v1/storage/`
		});
	const properties = {
		inline: true,
		restrictions: image_restrictions
	};
	const audio_properties = {
		inline: true,
		restrictions: audio_restrictions
	};

	const select_file_upload_type = (
		upload_type: AvailableUploadTypes.Image | AvailableUploadTypes.Audio
	) => {
		uppy.setOptions({
			restrictions:
				upload_type === AvailableUploadTypes.Audio ? audio_restrictions : image_restrictions
		});
		selected_type = upload_type;
	};
	let image_id: string;
	let youtube_url = $state('');
	let youtube_error = $state(false);

	const youtube_id_pattern = /^[A-Za-z0-9_-]{11}$/;
	const youtube_path_pattern = /^\/(?:embed|shorts)\/([A-Za-z0-9_-]{11})(?:\/|$)/;
	const youtube_upload_enabled = $derived(
		selected_question !== undefined && selected_question !== -1
	);

	const reset_youtube_form = () => {
		youtube_url = '';
		youtube_error = false;
	};

	const reset_selection = () => {
		selected_type = null;
		reset_youtube_form();
	};

	const extract_youtube_id = (input: string): string | undefined => {
		const value = input.trim();
		if (youtube_id_pattern.test(value)) {
			return value;
		}

		try {
			const url = new URL(value);
			const hostname = url.hostname.replace(/^www\./, '');
			if (hostname === 'youtu.be') {
				const id = url.pathname.split('/').filter(Boolean)[0];
				return id && youtube_id_pattern.test(id) ? id : undefined;
			}
			if (hostname === 'youtube.com' || hostname === 'm.youtube.com') {
				const watch_id = url.searchParams.get('v');
				if (watch_id && youtube_id_pattern.test(watch_id)) {
					return watch_id;
				}
				return url.pathname.match(youtube_path_pattern)?.[1];
			}
		} catch {
			return undefined;
		}

		return undefined;
	};

	const set_youtube_video = () => {
		if (selected_question === undefined || selected_question === -1) {
			return;
		}

		const youtube_id = extract_youtube_id(youtube_url);
		if (!youtube_id) {
			youtube_error = true;
			return;
		}

		data.questions[selected_question].image = `youtube:${youtube_id}`;
		modalOpen = false;
		reset_selection();
	};
	uppy.on('upload-success', (_file, response) => {
		image_id = response.body.id;
	});
	uppy.on('complete', (_) => {
		if (selected_question === undefined) {
			data.cover_image = image_id;
		} else if (selected_question === -1) {
			data.background_image = image_id;
		} else {
			data.questions[selected_question].image = image_id;
		}

		modalOpen = false;
		reset_selection();
	});

	onMount(() => {
		window.addEventListener('storage', (e) => {
			if (e.key !== 'video_upload_id') {
				return;
			}
			localStorage.removeItem('video_upload_id');
			data.questions[selected_question].image = e.newValue;
			reset_selection();
		});
	});

	const upload_video = async () => {
		video_popup = window.open(
			'/edit/videos',
			'_blank',
			'popup=true,toolbar=false,menubar=false,location=false,'
		);
		video_popup.addEventListener('beforeunload', () => {
			video_popup = undefined;
		});
	};

	const handle_on_click = (e: Event) => {
		if (e.target === e.currentTarget) {
			modalOpen = false;
			reset_selection();
		}
	};
	onMount(() => {
		window.addEventListener('keydown', (e: KeyboardEvent) => {
			if (e.key === 'Escape') {
				modalOpen = false;
				reset_selection();
			}
		});
	});
</script>

{#if modalOpen}
	<div
		class="w-screen h-screen fixed top-0 left-0 bg-cq-text/50 z-20 flex justify-center"
		onclick={handle_on_click}
		tabindex="0"
		role="button"
		aria-label="Close modal"
		onkeydown={(e) => (e.key === 'Enter' || e.key === ' ' ? handle_on_click(e) : null)}
		transition:fade={{ duration: 100 }}
	>
		{#if selected_type === null}
			<div class="cq-card m-auto w-1/3 h-auto p-4">
				<h1 class="text-3xl text-center mb-4">{$t('uploader.select_upload_type')}</h1>
				<div class="flex flex-row gap-4">
					<div class="w-full">
						<BrownButton
							onclick={() => {
								select_file_upload_type(AvailableUploadTypes.Image);
							}}
							>{$t('words.image')}
						</BrownButton>
					</div>
					<div class="w-full">
						<BrownButton
							disabled={!video_upload}
							onclick={() => {
								selected_type = AvailableUploadTypes.Video;
							}}
							>{$t('words.video')}
						</BrownButton>
					</div>
					{#if video_upload}
						<div class="w-full">
							<BrownButton
								onclick={() => {
									select_file_upload_type(AvailableUploadTypes.Audio);
								}}
								>{$t('words.audio')}
							</BrownButton>
						</div>
					{/if}
					{#if youtube_upload_enabled}
						<div class="w-full">
							<BrownButton
								onclick={() => {
									selected_type = AvailableUploadTypes.YouTube;
								}}
								>{$t('words.youtube')}
							</BrownButton>
						</div>
					{/if}
					{#if library_enabled}
						<div class="w-full">
							<BrownButton
								onclick={() => {
									selected_type = AvailableUploadTypes.Library;
								}}
								>{$t('words.library')}
							</BrownButton>
						</div>
					{/if}
					<div class="w-full">
						<BrownButton
							onclick={() => {
								selected_type = AvailableUploadTypes.Pixabay;
							}}
							>Pixabay
						</BrownButton>
					</div>
				</div>
			</div>
		{:else if selected_type === AvailableUploadTypes.Image}
			<div class="m-auto w-1/3 h-5/6" transition:fade={{ duration: 100 }}>
				<div>
					<SvelteDashboard {uppy} props={properties} />
				</div>
			</div>
		{:else if selected_type === AvailableUploadTypes.Audio}
			<div class="m-auto w-1/3 h-5/6" transition:fade={{ duration: 100 }}>
				<div>
					<SvelteDashboard {uppy} props={audio_properties} />
				</div>
			</div>
		{:else if selected_type === AvailableUploadTypes.Video}
			<div class="cq-card m-auto w-1/3 h-auto p-4" transition:fade={{ duration: 100 }}>
				<h1 class="text-3xl text-center mb-4">{$t('uploader.upload_a_video')}</h1>
				{#if video_popup}
					<p class="text-center">
						{$t('uploader.upload_video_popup_notice')}
					</p>
				{:else}
					<BrownButton onclick={upload_video} type="button"
						>{$t('uploader.upload_video')}</BrownButton
					>
				{/if}
			</div>
		{:else if selected_type === AvailableUploadTypes.YouTube}
			<form
				class="cq-card m-auto flex w-1/3 flex-col gap-3 p-4"
				transition:fade={{ duration: 100 }}
				onsubmit={(e) => {
					e.preventDefault();
					set_youtube_video();
				}}
			>
				<h1 class="text-3xl text-center">{$t('uploader.add_youtube_video')}</h1>
				<div class="cq-surface-muted flex flex-col gap-2 p-3">
					<label for="youtube-url" class="text-sm text-cq-muted">
						{$t('uploader.youtube_url_label')}
					</label>
					<input
						id="youtube-url"
						type="text"
						class="cq-surface w-full p-2 outline-hidden ring-2 ring-cq-border focus:ring-cq-brand"
						bind:value={youtube_url}
						placeholder="https://youtu.be/dQw4w9WgXcQ"
						oninput={() => (youtube_error = false)}
					/>
					{#if youtube_error}
						<p class="text-sm text-cq-muted" aria-live="polite">
							{$t('uploader.youtube_invalid')}
						</p>
					{/if}
				</div>
				<BrownButton type="submit">{$t('words.save')}</BrownButton>
			</form>
		{:else if selected_type === AvailableUploadTypes.Library}
			<div>
				<Library bind:data {selected_question} bind:modalOpen />
			</div>
		{:else if selected_type === AvailableUploadTypes.Pixabay}
			<div>
				<Pixabay bind:data {selected_question} bind:modalOpen />
			</div>
		{/if}
	</div>
{/if}
<div class="flex justify-center w-full pt-10" transition:fade>
	<button
		class="action-button flex w-1/2 justify-center"
		type="button"
		onclick={() => {
			modalOpen = true;
		}}
		><span class="italic">{$t('uploader.add_image')}</span>
		<svg
			class="w-6 h-6 inline-block"
			fill="none"
			stroke="currentColor"
			viewBox="0 0 24 24"
			xmlns="http://www.w3.org/2000/svg"
		>
			<path
				stroke-linecap="round"
				stroke-linejoin="round"
				stroke-width="2"
				d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
			/>
		</svg>
	</button>
</div>
