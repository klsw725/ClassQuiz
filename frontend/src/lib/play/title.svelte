<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import { getLocalization } from '$lib/i18n';

	interface Props {
		title: string;
		description: string;
		cover_image: string | undefined;
	}

	const { t } = getLocalization();

	let { title, description, cover_image }: Props = $props();
</script>

<div class="flex min-h-svh w-screen items-center justify-center p-6 text-cq-text">
	<div class="cq-card flex w-full max-w-5xl flex-col items-center p-8 text-center lg:p-10">
		<h1 class="text-5xl font-bold text-cq-text lg:text-7xl notranslate" translate="no">
			{@html title}
		</h1>
		<p class="pt-6 text-3xl text-cq-muted lg:text-4xl notranslate" translate="no">
			{@html description}
		</p>
		{#if cover_image}
			<div class="cq-surface-muted mt-10 flex max-h-[32vh] w-fit items-center justify-center p-3">
				<img
					class="block max-h-[30vh] max-w-full"
					src="/api/v1/storage/download/{cover_image}"
					alt={$t('media.not_available')}
				/>
			</div>
		{/if}
	</div>
</div>
