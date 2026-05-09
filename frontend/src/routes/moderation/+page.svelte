<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import type { PageData } from './$types';
	import BrownButton from '$lib/components/buttons/brown.svelte';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();
</script>

<div class="flex flex-col gap-4 p-2 text-cq-text">
	{#each data.quizzes as quiz}
		<div
			class="cq-card cq-card-interactive flex w-full flex-col gap-3 overflow-hidden p-3 lg:min-h-[20vh]"
		>
			<div class="grid h-full grid-cols-1 gap-4 lg:grid-cols-3">
				<div
					class="cq-surface-muted relative hidden h-full w-auto items-center justify-center overflow-hidden p-2 lg:flex"
				>
					{#if quiz.cover_image}
						<img
							src="/api/v1/storage/download/{quiz.cover_image}"
							alt="user provided"
							loading="lazy"
							class="max-h-full max-w-full shrink-0 rounded-md object-contain"
						/>
					{/if}
				</div>
				<div class="mx-auto my-auto max-h-full overflow-hidden">
					<p class="text-center text-xl text-cq-text">{@html quiz.title}</p>
					<p class="overflow-hidden text-clip text-center text-sm text-cq-muted">
						{@html quiz.description ?? ''}
					</p>
				</div>
				<div class="flex justify-center text-cq-muted">
					<p class="m-auto">Questions: {quiz.questions.length}</p>
				</div>
			</div>
			<div class="flex w-full">
				<BrownButton href="/view/{quiz.id}?mod=true&autoExpand=true&autoReturn=true"
					>View</BrownButton
				>
			</div>
		</div>
	{/each}
</div>
<div class="flex py-4 text-cq-text">
	<div class="cq-surface-muted mx-auto grid grid-cols-3 gap-3 p-3">
		<BrownButton disabled={data.page === '1'} href="/moderation?page={parseInt(data.page) + 1}"
			>Previous Page</BrownButton
		>
		<p class="m-auto text-cq-muted">Page {data.page}</p>
		<BrownButton
			disabled={data.quizzes.length !== 20}
			href="/moderation?page={parseInt(data.page) - 1}">Next Page</BrownButton
		>
	</div>
</div>
