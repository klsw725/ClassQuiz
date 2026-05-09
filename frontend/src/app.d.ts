// SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)
//
// SPDX-License-Identifier: MPL-2.0

/// <reference types="@sveltejs/kit" />

export {};

// See https://kit.svelte.dev/docs/types#app
// for information about these interfaces
// and what to do when importing types
declare global {
	namespace App {
		interface Locals {
			email: string | null;
		}

		// interface Platform {}

		// interface Stuff {}
	}
}

interface HCaptcha {
	execute: (widgetId?: unknown, options?: unknown) => Promise<{ response: string }>;
	render: (container: string | HTMLElement, options: Record<string, unknown>) => unknown;
}

interface ReCaptcha {
	ready: (callback: () => void) => void;
	execute: (siteKey: string, options: { action: string }) => Promise<string>;
}

declare global {
	interface Window {
		hcaptcha: HCaptcha;
		grecaptcha: ReCaptcha;
	}

	const grecaptcha: ReCaptcha;
}

declare module 'yup' {
	export function reach(
		schema: object,
		path: string,
		value?: unknown,
		context?: unknown
	): {
		isValidSync: (value: unknown) => boolean;
	};
}

declare module 'svelte/motion' {
	export interface SpringOpts {
		stiffness?: number;
		damping?: number;
		precision?: number;
	}
}
