<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import type { Markdown } from '$lib/quiztivity/types';
	import { marked } from 'marked';
	import { browser } from '$app/environment';

	interface Props {
		data: Markdown | undefined;
	}

	let { data = $bindable() }: Props = $props();

	if (!data) {
		data = {
			markdown: ''
		};
	}

	let rendered_html = $derived(browser ? marked.parse(data.markdown) : '');
</script>

<div class="w-full h-[70vh] flex flex-row p-4 gap-4">
	<textarea
		class="w-full resize-none cq-surface outline-hidden p-2 placeholder:text-cq-muted"
		bind:value={data.markdown}
		placeholder="Enter your markdown here!"
	></textarea>
	<div class="w-full">
		<div
			class="aspect-video prose max-w-none cq-surface p-2 dark:prose-invert"
		>
			{@html rendered_html}
		</div>
	</div>
</div>
