<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import { fly } from 'svelte/transition';
	import { getLocalization } from '$lib/i18n';
	import { PopoverTypes } from './smalltop';

	const { t } = getLocalization();

	interface Props {
		open?: boolean;
		type: PopoverTypes;
		data?: undefined | { game_pin: number | string; game_id: string } | string;
	}

	let { open = $bindable(false), type, data = undefined }: Props = $props();
</script>

{#if open}
	<div
		class="fixed w-screen top-10 z-[60] flex justify-center"
		transition:fly|global={{ y: -100 }}
	>
		<div
			class="cq-card flex w-full max-w-xs items-center p-4 text-cq-muted"
			role="alert"
		>
			<div class="ml-3 text-sm font-normal">
				{#if type === PopoverTypes.Copy}
					{$t('components.popover.copied_to_clipboard')}
				{:else if type === PopoverTypes.GameInLobby && data && typeof data !== 'string'}A game is currently in the lobby. Click <a
						class="link-hover underline"
						href="/remote?game_pin={data.game_pin}&game_id={data.game_id}">here</a
					> to join as a remote.
				{:else if type === PopoverTypes.Generic}
					{@html data}
				{:else}
					<p>Error!!!</p>
				{/if}
			</div>
			<button
				type="button"
				class="cq-surface-muted -my-1.5 -mx-1.5 ml-auto inline-flex h-8 w-8 p-1.5 text-cq-muted hover:text-cq-text focus:ring-2 focus:ring-cq-brand"
				data-dismiss-target="#toast-default"
				aria-label="Close"
				onclick={() => {
					open = false;
				}}
			>
				<span class="sr-only">{$t('words.close')}</span>
				<svg
					aria-hidden="true"
					class="w-5 h-5"
					fill="currentColor"
					viewBox="0 0 20 20"
					xmlns="http://www.w3.org/2000/svg"
				>
					<path
						fill-rule="evenodd"
						d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
						clip-rule="evenodd"
					/>
				</svg>
			</button>
		</div>
	</div>
{/if}
