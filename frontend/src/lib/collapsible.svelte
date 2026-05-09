<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">

	interface Props {
		headerText: any;
		expanded?: boolean;
		children?: import('svelte').Snippet;
	}

	let { headerText, expanded = $bindable(false), children }: Props = $props();
</script>

<div>
	<h3 class="bg-transparent m-0">
		<button
			aria-expanded={expanded}
			onclick={() => (expanded = !expanded)}
			class="cq-surface cq-card-interactive flex justify-between w-full m-0 p-2 rounded-t-lg transition"
			class:rounded-b-lg={!expanded}
			><span>{@html headerText}</span>
			<svg
				viewBox="0 0 20 20"
				fill="none"
				class="my-auto fill-current text-cq-text"
				stroke="currentColor"
			>
				<path class="vert" d="M10 1V19" stroke-width="2" stroke="currentColor" />
				<path d="M1 10L19 10" stroke-width="2" stroke="currentColor" />
			</svg>
		</button>
	</h3>

	<div class:hidden={!expanded}>
		{@render children?.()}
	</div>
</div>

<style>
	/*	h3 {
		margin: 0;
	}

	button {
		background-color: var(--background, #fff);
		color: var(--gray-darkest, #282828);
		display: flex;
		justify-content: space-between;
		width: 100%;
		border: none;
		margin: 0;
		padding: 1em 0.5em;
	}*/
	button {
	}

	button[aria-expanded='true'] {
		border-bottom: 1px solid var(--gray-light, #eee);
	}

	button[aria-expanded='true'] .vert {
		display: none;
	}

	button:focus svg {
		outline: 2px solid;
	}

	svg {
		height: 0.7em;
		width: 0.7em;
	}
</style>
