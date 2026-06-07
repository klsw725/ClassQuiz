<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import { goto } from '$app/navigation';
	import type { PageData } from './$types';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();
	let input_data = $state({
		player_name: data.username,
		name: ''
	});

	let isValid = $derived(input_data.name.length !== 0 && input_data.player_name.length >= 2);
	let isSubmitting = false;

	const submit = async (e: Event) => {
		e.preventDefault();
		if (!isValid) {
			return;
		}
		const res = await fetch('/api/v1/box-controller/web/setup', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify(input_data)
		});
		if (res.ok) {
			const json = await res.json();
			goto(`/account/controllers/add/wait?id=${json.id}&code=${json.code}`);
		}
	};
</script>

<div class="flex min-h-screen items-center justify-center px-4 py-10 text-cq-text">
	<div class="w-full max-w-md">
		<div class="cq-card mx-auto w-full overflow-hidden">
			<div class="px-6 py-4">
				<h2 class="text-center text-3xl font-bold text-cq-text">ClassQuiz</h2>

				<h3 class="mt-1 text-center text-xl font-medium text-cq-muted">Add a controller</h3>

				<form onsubmit={submit}>
					<div class="mt-4 flex w-full flex-col gap-4">
						<div class="cq-surface-muted p-4">
							<div class="relative w-full bg-inherit">
								<input
									id="player_name"
									name="player_name"
									type="text"
									class="peer h-10 w-full rounded-lg bg-transparent px-2 text-cq-text placeholder-transparent ring-2 ring-cq-border focus:ring-cq-brand focus:outline-hidden"
									class:ring-red-700={input_data.player_name.length < 2}
									class:ring-green-600={input_data.player_name.length >= 2}
									bind:value={input_data.player_name}
								/>
								<label
									for="player_name"
									class="absolute -top-3 left-0 mx-1 cursor-text bg-inherit px-1 text-sm text-cq-text transition-all peer-placeholder-shown:top-2 peer-placeholder-shown:text-base peer-placeholder-shown:text-cq-muted peer-focus:-top-3 peer-focus:text-sm peer-focus:text-cq-text"
								>
									Player name
								</label>
							</div>
						</div>
						<div class="cq-surface-muted p-4">
							<div class="relative w-full bg-inherit">
								<input
									id="name"
									name="name"
									type="text"
									class="peer h-10 w-full rounded-lg bg-transparent px-2 text-cq-text placeholder-transparent ring-2 ring-cq-border focus:ring-cq-brand focus:outline-hidden"
									placeholder="Name"
									class:ring-red-700={input_data.name.length === 0}
									class:ring-green-600={input_data.name.length !== 0}
									bind:value={input_data.name}
								/>
								<label
									for="name"
									class="absolute -top-3 left-0 mx-1 cursor-text bg-inherit px-1 text-sm text-cq-text transition-all peer-placeholder-shown:top-2 peer-placeholder-shown:text-base peer-placeholder-shown:text-cq-muted peer-focus:-top-3 peer-focus:text-sm peer-focus:text-cq-text"
								>
									Name
								</label>
							</div>
						</div>

						<div class="mt-2 flex items-center justify-center">
							<button
								class="accent-button w-fit"
								disabled={!isValid || isSubmitting}
								class:cursor-not-allowed={!isValid || isSubmitting}
								class:opacity-50={!isValid || isSubmitting}
								type="submit"
							>
								{#if isSubmitting}
									<svg class="h-4 w-4 animate-spin" viewBox="3 3 18 18">
										<path
											class="fill-cq-text"
											d="M12 5C8.13401 5 5 8.13401 5 12C5 15.866 8.13401 19 12 19C15.866 19 19 15.866 19 12C19 8.13401 15.866 5 12 5ZM3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12Z"
										/>
										<path
											class="fill-cq-surface"
											d="M16.9497 7.05015C14.2161 4.31648 9.78392 4.31648 7.05025 7.05015C6.65973 7.44067 6.02656 7.44067 5.63604 7.05015C5.24551 6.65962 5.24551 6.02646 5.63604 5.63593C9.15076 2.12121 14.8492 2.12121 18.364 5.63593C18.7545 6.02646 18.7545 6.65962 18.364 7.05015C17.9734 7.44067 17.3403 7.44067 16.9497 7.05015Z"
										/>
									</svg>
								{:else}
									Add
								{/if}
							</button>
						</div>
					</div>
				</form>
			</div>

			<div
				class="cq-surface-muted flex items-center justify-center rounded-none border-x-0 border-b-0 py-4 text-center"
			>
				<span class="text-sm text-cq-muted">Don't know what this is? </span>

				<a
					href="/controller"
					class="link-hover mx-2 text-sm font-bold text-cq-text underline decoration-cq-border underline-offset-4"
					>Read more here.</a
				>
			</div>
		</div>
	</div>
</div>
