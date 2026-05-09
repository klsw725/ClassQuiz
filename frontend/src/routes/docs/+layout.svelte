<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import Footer from '$lib/footer.svelte';
	import { navbarVisible } from '$lib/stores.svelte.ts';
	interface Props {
		children?: import('svelte').Snippet;
	}

	let { children }: Props = $props();

	navbarVisible.visible = true;
</script>

<div class="flex min-h-screen flex-col text-cq-text">
	<main class="flex-1 px-4 pb-10 sm:px-6 lg:px-8">
		{@render children?.()}
	</main>
	<div class="pt-4">
		<Footer />
	</div>
</div>
