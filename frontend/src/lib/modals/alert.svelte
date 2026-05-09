<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<!--
By Flowbite, but changed: https://flowbite.com/docs/components/modal/#default-modal
-->
<script lang="ts">
	interface Props {
		title: string;
		body: string;
		open: boolean;
	}

	let { title, body, open = $bindable() }: Props = $props();
	console.log(open, title, body);
	open = true;
</script>

<!-- Main modal -->
{#if open}
	<div tabindex="-1" class="overflow-y-auto overflow-x-hidden md:inset-0 lg:w-2/6 w-5/6">
		<div class="relative p-4 w-full max-w-2xl h-full md:h-auto">
			<!-- Modal content -->
			<div class="cq-card relative">
				<!-- Modal header -->
				<div
					class="flex items-start justify-between rounded-t border-b border-cq-border p-4"
				>
					<h3 class="text-xl font-semibold text-cq-text">
						{title}
					</h3>
					<button
						type="button"
						class="cq-surface-muted ml-auto inline-flex items-center p-1.5 text-sm text-cq-muted hover:text-cq-text"
						onclick={() => {
							open = false;
						}}
					>
						<svg
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
				<!-- Modal body -->
				<div class="p-6 space-y-6">
					<p class="text-base leading-relaxed text-cq-muted">
						{body}
					</p>
				</div>
				<!-- Modal footer -->
				<div
					class="flex items-center space-x-2 rounded-b border-t border-cq-border p-6"
				>
					<button
						data-modal-toggle="defaultModal"
						type="button"
						onclick={() => {
							open = false;
						}}
						class="accent-button w-fit text-sm font-medium"
					>
						Close
					</button>
				</div>
			</div>
		</div>
	</div>
{/if}
