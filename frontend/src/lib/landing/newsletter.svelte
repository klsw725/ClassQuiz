<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	interface Props {
		open: boolean;
	}

	let { open = $bindable() }: Props = $props();

	const closeThing = () => {
		open = false;
		localStorage.setItem('newsletter', 'closed');
	};
</script>

<form method="post" action="https://newsletter.mawoka.eu/subscription/form" class="bg-transparent">
	<div class="absolute top-1 right-1">
		<button type="button" class="text-cq-muted hover:text-cq-text" onclick={closeThing}>
			<svg
				class="w-6 h-6"
				fill="none"
				stroke="currentColor"
				viewBox="0 0 24 24"
				xmlns="http://www.w3.org/2000/svg"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
				/>
			</svg>
		</button>
	</div>
	<div>
		<h3 class="text-lg font-semibold text-cq-text">ClassQuiz-Newsletter</h3>
		<input type="hidden" name="nonce" />
		<p>
			<input
				type="email"
				name="email"
				required
				placeholder="E-mail"
				class="m-0.5 rounded-lg border-b-2 border-cq-border bg-transparent p-0.5 text-cq-text outline-hidden placeholder:text-cq-muted focus:outline-cq-border"
			/>
		</p>
		<p>
			<input
				type="text"
				name="name"
				placeholder="Name (optional)"
				class="m-0.5 rounded-lg border-b-2 border-cq-border bg-transparent p-0.5 text-cq-text outline-hidden placeholder:text-cq-muted focus:outline-cq-border"
			/>
		</p>

		<p class="hidden">
			<input
				id="fec55"
				type="checkbox"
				name="l"
				checked
				value="fec5595e-9af1-497a-b7eb-1edd7ad2e21c"
			/>
			<label for="fec55">ClassQuiz-News</label>
		</p>
		<button type="submit" class="accent-button w-fit">Subscribe!</button>
	</div>
</form>
