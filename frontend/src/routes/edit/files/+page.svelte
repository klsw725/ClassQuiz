<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import type { PageData } from './$types';
	import { fade } from 'svelte/transition';
	import MediaComponent from '$lib/editor/MediaComponent.svelte';
	import BrownButton from '$lib/components/buttons/brown.svelte';
	import { onMount } from 'svelte';
	import Uploader from './uploader.svelte';
	import { getLocalization } from '$lib/i18n';

	const { t } = getLocalization();

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();
	let edit_popup = $state(null);
	const images = data.images;

	const close_popup_handler = (e: Event) => {
		if (e.target !== e.currentTarget) return;
		edit_popup = null;
	};
	onMount(() => {
		window.onkeydown = (e: KeyboardEvent) => {
			if (e.key === 'Escape') {
				edit_popup = null;
			}
		};
	});

	const save_image_metadata = async (e: Event) => {
		e.preventDefault();
		await fetch(`/api/v1/storage/meta/${edit_popup.id}`, {
			method: 'PUT',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({ filename: edit_popup.filename, alt_text: edit_popup.alt_text })
		});
		edit_popup = null;
		window.location.reload();
	};

	const delete_image = async (id: string) => {
		await fetch(`/api/v1/storage/meta/${id}`, { method: 'DELETE' });
		window.location.reload();
	};
</script>

<div>
	<h2 class="text-center text-4xl">
		{$t('file_dashboard.storage_usage', {
			used: (data.storage_usage.used / (1024 * 1024)).toFixed(2),
			total: (data.storage_usage.limit / (1024 * 1024)).toFixed(0),
			percent: ((data.storage_usage.used / data.storage_usage.limit) * 100).toFixed(0)
		})}
	</h2>
	<Uploader />
	<div class="grid grid-cols-1 lg:grid-cols-2 p-4 gap-4">
		{#each images as image}
			<div
				class="cq-card p-2 grid grid-cols-2 hover:opacity-100 transition-all"
				class:opacity-40={image.quiztivities.length === 0 && image.quizzes.length === 0}
			>
				<MediaComponent
					src={image.id}
					css_classes="m-auto h-auto w-auto max-h-[30vh]"
				/>
				<div class="flex flex-col my-auto ml-4">
					<p>
						{$t('file_dashboard.size', {
							size: (image.size / (1024 * 1024)).toFixed(2)
						})}
					</p>
					<p>
						{$t('file_dashboard.caption', {
							caption: image.alt_text ?? $t('file_dashboard.missing')
						})}
					</p>
					<p>
						{$t('file_dashboard.filename', {
							filename: image.filename ?? $t('file_dashboard.missing')
						})}
					</p>
					<p>
						{$t('file_dashboard.uploaded', {
							date: new Date(image.uploaded_at).toLocaleString()
						})}
					</p>
					<p>
						{$t('file_dashboard.imported', {
							yes_or_no: image.imported ? $t('words.yes') : $t('words.no')
						})}
					</p>
					<div class="flex flex-col gap-2">
						<BrownButton
							onclick={() => {
								edit_popup = image;
							}}
							>{$t('file_dashboard.edit_details')}
						</BrownButton>
						{#if image.quiztivities.length === 0 && image.quizzes.length === 0}
							<BrownButton
								onclick={() => {
									delete_image(image.id);
								}}>{$t('file_dashboard.delete_image')}</BrownButton
							>
						{/if}
					</div>
				</div>
			</div>
		{/each}
	</div>
</div>

{#if edit_popup}
	<div
		transition:fade={{ duration: 100 }}
		class="fixed top-0 left-0 h-screen w-screen z-40 flex bg-cq-text/50"
		onclick={close_popup_handler}
	>
		<div class="cq-card w-auto h-auto m-auto p-4">
			<h1 class="text-2xl text-center">{$t('file_dashboard.edit_the_image')}</h1>
			<form class="flex flex-col" onsubmit={save_image_metadata}>
				<div class="flex flex-row">
					<div class="flex flex-col mr-4">
						<label for="name" class="m-auto">{$t('file_dashboard.filename_word')}</label
						>
						<label for="alt_text" class="m-auto">{$t('file_dashboard.alt_text')}</label>
					</div>
					<div class="flex flex-col gap-3">
						<input
							class="rounded-lg bg-cq-surface outline-hidden p-0.5 border-4 border-transparent"
							id="name"
							type="text"
							bind:value={edit_popup.filename}
						/>
						<input
							class:border-red-700={!edit_popup.alt_text}
							class="transition rounded-lg bg-cq-surface outline-hidden p-0.5 border-4 border-transparent"
							id="alt_text"
							type="text"
							bind:value={edit_popup.alt_text}
						/>
					</div>
				</div>
				<div class="mt-4">
					<BrownButton type="submit">{$t('words.save')}</BrownButton>
				</div>
			</form>
		</div>
	</div>
{/if}
