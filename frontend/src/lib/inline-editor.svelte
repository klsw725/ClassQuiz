<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import {
		Autoformat,
		BalloonEditor,
		Bold,
		Essentials,
		HorizontalLine,
		Italic,
		Paragraph,
		Strikethrough,
		Subscript,
		Superscript,
		TextTransformation,
		Underline
	} from 'ckeditor5';
	import 'ckeditor5/ckeditor5.css';
	import { onMount } from 'svelte';
	import { run } from 'svelte/legacy';

	const triggerChange = () => {
		text = editor.getData();
	};

	interface Props {
		// import Autoformat from "@ckeditor/ckeditor5-autoformat/src/autoformat"
		text?: string;
		horizontalLine?: boolean;
	}

	let { text = $bindable(''), horizontalLine = false }: Props = $props();

	let html_el = $state<HTMLElement>();

	run(() => {
		text = text.replace('<p>', '').replace('</p>', '');
	});
	let editor: Awaited<ReturnType<typeof BalloonEditor.create>>;
	onMount(() => {
		const builtinPlugins = [
			Essentials,
			Autoformat,
			Bold,
			Italic,
			Paragraph,
			TextTransformation,
			Strikethrough,
			Subscript,
			Superscript,
			Underline,
			...(horizontalLine ? [HorizontalLine] : [])
		];
		const toolbar = [
			'bold',
			'italic',
			'underline',
			'strikethrough',
			'superscript',
			'subscript',
			...(horizontalLine ? ['horizontalLine'] : []),
			'|',
			'undo',
			'redo'
		];

		if (!html_el) {
			return;
		}
		BalloonEditor.create(html_el, {
			licenseKey: 'GPL',
			plugins: builtinPlugins,
			toolbar,
			language: 'en'
		})
			.then((newEditor) => {
				editor = newEditor;
				editor.setData(text);
				editor.model.document.on('change:data', () => {
					triggerChange();
				});
			})
			.catch((error) => {
				console.error('There was a problem initializing the editor.', error);
			});
	});
</script>

<div class="w-fit rounded-lg border-cq-border border">
	<div
		bind:this={html_el}
		contenteditable="true"
		class="rounded-lg border-cq-border border text-center w-fit h-fit resize-none bg-cq-surface min-w-[5rem] text-cq-text"
	></div>
</div>

<style>
	:global(.ck-powered-by) {
		display: none;
	}
</style>
