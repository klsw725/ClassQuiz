<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import BrownButton from '$lib/components/buttons/brown.svelte';
	import { fade, fly } from 'svelte/transition';
	import { bounceOut } from 'svelte/easing';
	import Spinner from '$lib/Spinner.svelte';
	import { getLocalization } from '$lib/i18n';

	const { t } = getLocalization();

	const item_count = {
		skin_color: 7,
		top_type: 35,
		hair_color: 10,
		facial_hair_type: 6,
		facial_hair_color: 10,
		mouth_type: 12,
		eyebrow_type: 13,
		accessories_type: 7,
		hat_color: 15,
		clothe_type: 9,
		clothe_color: 15,
		clothe_graphic_type: 11
	};

	const translation_map = {
		skin_color: $t('avatar_settings.skin_color'),
		top_type: $t('avatar_settings.top_type'),
		hair_color: $t('avatar_settings.hair_color'),
		facial_hair_type: $t('avatar_settings.facial_hair_type'),
		facial_hair_color: $t('avatar_settings.facial_hair_color'),
		mouth_type: $t('avatar_settings.mouth_type'),
		eyebrow_type: $t('avatar_settings.eyebrow_type'),
		accessories_type: $t('avatar_settings.accessories_type'),
		hat_color: $t('avatar_settings.hat_color'),
		clothe_type: $t('avatar_settings.clothe_type'),
		clothe_color: $t('avatar_settings.clothe_color'),
		clothe_graphic_type: $t('avatar_settings.clothe_graphic_type')
	};

	let data = $state({
		skin_color: 0,
		top_type: 0,
		hair_color: 0,
		facial_hair_type: 0,
		facial_hair_color: 0,
		mouth_type: 0,
		eyebrow_type: 0,
		accessories_type: 0,
		hat_color: 0,
		clothe_type: 0,
		clothe_color: 0,
		clothe_graphic_type: 0
	});

	const data_keys = Object.keys(data);
	let index = $state(0);
	// let index = 10;
	let save_finished: undefined | boolean = $state(undefined);
	let finished = $state(false);
	const get_image_url = (input_data) => {
		return `/api/v1/avatar/custom?${new URLSearchParams(Object.entries(input_data).map(([key, value]) => [key, String(value)])).toString()}`;
	};

	let image_url = $derived(get_image_url(data));

	const save_avatar = async () => {
		save_finished = false;
		const res = await fetch(`/api/v1/avatar/save?${new URLSearchParams(Object.entries(data).map(([key, value]) => [key, String(value)])).toString()}`, {
			method: 'POST'
		});
		if (res.ok) {
			save_finished = true;
		}
	};
</script>

<div class="min-h-screen p-4 text-cq-text md:p-6">
	<div class="cq-card grid gap-4 p-4 lg:grid-cols-4">
		<div
			class="cq-surface-muted flex flex-col items-center justify-center gap-4 p-4 lg:col-span-1"
		>
			<img
				class="cq-surface aspect-square w-full max-w-72 object-contain p-3"
				src={image_url}
				alt={$t('settings_page.change_avatar')}
			/>
			<p class="text-center text-sm text-cq-muted">
				{translation_map[data_keys[index]]} ({index + 1}/{data_keys.length})
			</p>
		</div>
		<div class="flex min-h-0 flex-col gap-4 lg:col-span-3">
			<div class="cq-surface-muted grid gap-3 p-3 md:grid-cols-3 md:items-center">
				<div class="flex justify-start">
					<BrownButton
						onclick={() => {
							index = index - 1;
						}}
						disabled={index < 1}>{$t('words.back')}</BrownButton
					>
				</div>
				<div class="text-center">
					<h2 class="text-2xl font-semibold text-cq-text">
						{translation_map[data_keys[index]]} ({index + 1}/{data_keys.length})
					</h2>
				</div>
				<div class="flex justify-end">
					<BrownButton disabled={index < 11}>{$t('words.finish')}</BrownButton>
				</div>
			</div>
			<div class="cq-surface min-h-0 overflow-y-auto p-3">
				<div class="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
					{#each Array.from(Array(item_count[data_keys[index]]).keys()) as key}
						<button
							type="button"
							class="cq-surface-muted cq-card-interactive aspect-square overflow-hidden border-cq-border p-2 hover:border-cq-brand focus:ring-2 focus:ring-cq-brand focus:outline-hidden"
							class:border-cq-brand={data[data_keys[index]] === key}
							class:ring-2={data[data_keys[index]] === key}
							class:ring-cq-brand={data[data_keys[index]] === key}
							onclick={() => {
								data[data_keys[index]] = key;
								if (index < 11) {
									index++;
								} else {
									save_finished = undefined;
									finished = true;
								}
							}}
						>
							<img
								class="h-full w-full object-contain"
								src={get_image_url({ ...data, [data_keys[index]]: key })}
								alt="{translation_map[data_keys[index]]} {key + 1}"
								in:fade|global={{ duration: 100 }}
							/>
						</button>
					{/each}
				</div>
			</div>
		</div>
	</div>
</div>
{#if finished}
	<div
		class="fixed inset-0 z-30 overflow-y-auto bg-cq-surface p-4 backdrop-blur-sm md:p-12"
		out:fade|global={{ duration: 200 }}
		in:fade|global={{ duration: 300 }}
	>
		<div class="mx-auto flex min-h-full w-full max-w-4xl items-center justify-center">
			<div class="cq-card flex w-full flex-col items-center gap-6 p-6 text-center">
				<h1 class="text-4xl font-semibold text-cq-text" in:fade|global={{ delay: 3500 }}>
					{$t('avatar_settings.thats_you')}
				</h1>
				<img
					class="cq-surface-muted z-20 aspect-square w-full max-w-md object-contain p-4"
					src={get_image_url(data)}
					alt={$t('avatar_settings.thats_you')}
					in:fly|global={{ delay: 500, duration: 4000, y: -500, easing: bounceOut }}
				/>
				<div class="grid w-full gap-3 sm:grid-cols-2" in:fade|global={{ delay: 3500 }}>
					<BrownButton
						onclick={() => {
							index = 0;
							finished = false;
						}}>{$t('avatar_settings.start_over')}</BrownButton
					>
					<BrownButton
						onclick={save_avatar}
						flex={true}
						disabled={save_finished === true}
					>
						{#if save_finished === undefined}{$t('words.save')}
						{:else if save_finished === true}
							<svg
								class="h-6 w-6"
								aria-hidden="true"
								fill="none"
								stroke="currentColor"
								stroke-width="2"
								viewBox="0 0 24 24"
								xmlns="http://www.w3.org/2000/svg"
							>
								<path
									d="M5 13l4 4L19 7"
									stroke-linecap="round"
									stroke-linejoin="round"
								/>
							</svg>
						{:else if save_finished === false}
							<Spinner my_20={false} />
						{/if}
					</BrownButton>
					<BrownButton href="/account/settings"
						>{$t('avatar_settings.go_back')}</BrownButton
					>
					<BrownButton
						onclick={() => {
							finished = false;
						}}>{$t('words.close')}</BrownButton
					>
				</div>
			</div>
		</div>
	</div>
{/if}
