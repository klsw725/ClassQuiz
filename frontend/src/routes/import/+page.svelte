<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import { getLocalization } from '$lib/i18n';
	import { navbarVisible } from '$lib/stores.svelte.ts';
	import { onMount } from 'svelte';
	import { page } from '$app/state';

	navbarVisible.visible = true;

	const { t } = getLocalization();
	let url_input = $state('');
	let file_input = $state();
	let kahoot_regex = /^https:\/\/create\.kahoot\.it\/details\/.*\/?([a-zA-Z-\d]{36})\/?$/;

	let url_valid = $derived(kahoot_regex.test(url_input));
	let is_loading = $state(false);

	const submit = async (e) => {
		e.preventDefault();
		if (!url_valid) {
			return;
		}
		is_loading = true;
		const regex_res = kahoot_regex.exec(url_input);
		const res = await fetch(`/api/v1/quiz/import/${regex_res[1]}`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			}
		});

		if (res.status === 200) {
			window.location.href = '/dashboard';
		} else if (res.status === 400) {
			/*			alertModal.set({
				open: true,
				title: 'Import failed',
				body: "This quiz isn't (yet) supported!"
			});*/
			alert("This quiz isn't (yet) supported!");
		} else if (res.status === 403) {
			/*			alertModal.set({
				open: true,
				title: 'Import failed',
				body: 'Unknown error while importing the quiz!'
			});*/
			alert('Quiz is probably private!');
		} else {
			alert(`Kahoot replied with ${res.status}`);
		}
		is_loading = false;
	};

	const file_submit = async (e) => {
		e.preventDefault();
		is_loading = true;
		const formdata = new FormData();
		formdata.append('file', file_input[0]);
		let res = new Response(null);
		if (file_input[0].name.includes('.xlsx')) {
			res = await fetch('/api/v1/quiz/excel-import', {
				method: 'POST',
				body: formdata
			});
		} else if (file_input[0].name.includes('.cqa')) {
			res = await fetch('/api/v1/eximport/', {
				method: 'POST',
				body: formdata
			});
		} else {
			alert('Wrong file type');
			is_loading = false;
			return;
		}

		if (res.status === 200) {
			window.location.href = '/dashboard';
		} else {
			/*			alertModal.set({
				open: true,
				title: 'Import failed',
				body: 'Something went wrong!'
			});*/
			alert('Something went wrong!');
		}
		is_loading = false;
	};

	onMount(() => {
		let url_from_path = page.url.searchParams.get('url');
		if (url_from_path === '') {
			url_from_path = null;
		}
		url_input = url_from_path ?? '';
	});
</script>

<svelte:head>
	<title>ClassQuiz - Import</title>
</svelte:head>

<div class="flex min-h-screen items-center justify-center px-4 py-10 text-cq-text">
	<div class="w-full max-w-5xl">
		<div class="cq-card mx-auto w-full overflow-hidden">
			<div class="px-6 py-5">
				<h2 class="text-center text-3xl font-bold text-cq-text">
					{$t('words.import')}
				</h2>

				<div class="grid grid-cols-1 gap-4 lg:grid-cols-2">
					<form onsubmit={submit}>
						<div class="mt-4 flex h-full w-full flex-col gap-4">
							<h2 class="text-center text-2xl text-cq-text">{$t('import_page.a_kahoot_quiz')}</h2>
							<div class="cq-surface-muted p-4">
								<div class="relative w-full bg-inherit">
									<input
										id="url"
										bind:value={url_input}
										name="email"
										type="url"
										class="peer h-10 w-full rounded-lg bg-transparent px-2 text-cq-text placeholder-transparent ring-2 ring-cq-border focus:ring-cq-brand focus:outline-hidden"
										placeholder="https://create.kahoot.it/details/something"
										class:ring-red-700={!url_valid}
										class:ring-green-600={url_valid}
									/>
									<label
										for="url"
										class="absolute -top-3 left-0 mx-1 cursor-text bg-inherit px-1 text-sm text-cq-text transition-all peer-placeholder-shown:top-2 peer-placeholder-shown:text-base peer-placeholder-shown:text-cq-muted peer-focus:-top-3 peer-focus:text-sm peer-focus:text-cq-text"
									>
										{$t('words.url')}
									</label>
									<p class="text-sm text-cq-muted">
										{$t('import_page.url_should_look_like_this')}
									</p>
								</div>
								<p class="mt-2 text-cq-muted">
									{$t('import_page.side_import_kahoot')}
								</p>
							</div>

							<div class="mt-auto flex items-center justify-center">
								<span></span>

								<button
									class="accent-button w-fit"
									disabled={!url_valid || is_loading}
									type="submit"
								>
									{#if is_loading}
										<svg
											class="mx-auto h-4 w-4 animate-spin"
											viewBox="3 3 18 18"
										>
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
										{$t('words.submit')}
									{/if}
								</button>
							</div>
						</div>
					</form>
					<form onsubmit={file_submit}>
						<div class="mt-4 flex h-full w-full flex-col gap-4 border-cq-border lg:border-l lg:pl-4">
							<h2 class="text-center text-2xl text-cq-text">{$t('import_page.classquiz_quiz')}</h2>
							<div class="cq-surface-muted p-4">
								<div class="relative w-full bg-inherit">
									<input
										id="file"
										bind:files={file_input}
										name="file"
										type="file"
										accept=".cqa,.xlsx"
										class="peer h-10 w-full rounded-lg bg-transparent px-2 py-1.5 text-cq-text placeholder-transparent ring-2 ring-cq-border focus:ring-cq-brand focus:outline-hidden"
										class:ring-red-700={!file_input || file_input.length === 0}
										class:ring-green-600={file_input && file_input.length > 0}
									/>
									<p class="text-sm text-cq-muted">{$t('import_page.upload_file_ending')}</p>
								</div>
								<p class="mt-2 text-cq-muted">
									{$t('import_page.this_side_classquiz')}
									<br />
									{$t('import_page.this_side_classquiz_excel')}
								</p>
								<a
									class="link-hover text-sm font-bold text-cq-muted underline"
									download
									href="https://blog.web.garage.realux.mawoka.eu/classquiz/ClassQuizImportTemplate.xlsx"
									>{$t('import_page.download_template_here')}</a
								>
							</div>

							<div class="mt-auto flex items-center justify-center">
								<span></span>

								<button
									class="accent-button w-fit"
									disabled={!file_input || file_input.length === 0 || is_loading}
									type="submit"
								>
									{#if is_loading}
										<svg
											class="mx-auto h-4 w-4 animate-spin"
											viewBox="3 3 18 18"
										>
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
										{$t('words.submit')}
									{/if}
								</button>
							</div>
						</div>
					</form>
				</div>
			</div>
			<div class="cq-surface-muted mt-4 flex items-center justify-center py-4 text-center">
				<span class="text-sm text-cq-muted"
					>{$t('import_page.need_help')}</span
				>

				<a
					href="/docs/import-from-kahoot"
					class="link-hover mx-2 text-sm font-bold text-cq-muted underline"
					>{$t('import_page.visit_docs')}</a
				>
			</div>
		</div>
	</div>
</div>
<!--{/if}-->
