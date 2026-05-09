<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import type { Markdown } from '$lib/quiztivity/types';
	import DOMPurify from 'dompurify';
	import { marked } from 'marked';
	import { browser } from '$app/environment';

	interface Props {
		data: Markdown | undefined;
	}

	let { data }: Props = $props();

	let rendered_html = $derived(
		browser ? DOMPurify.sanitize(marked.parse(data?.markdown ?? '', { async: false })) : ''
	);
</script>

<div class="p-4 text-cq-text">
	<div class="cq-card prose dark:prose-invert max-w-none p-6 text-cq-text">
		{@html rendered_html}
	</div>
</div>
