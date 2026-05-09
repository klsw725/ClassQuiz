<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import { onMount } from 'svelte';
	import '$lib/hljs.css';
	interface Props {
		children?: import('svelte').Snippet;
	}

	let { children }: Props = $props();

	onMount(async () => {
		const { default: hljs } = await import('highlight.js/lib/common');
		hljs.highlightAll();
	});
</script>

<article
	class="cq-card prose prose-sm sm:prose lg:prose-lg xl:prose-xl mx-auto mt-10 px-6 py-8 text-cq-text prose-slate dark:prose-invert sm:px-8 lg:px-10"
>
	{@render children?.()}
</article>
