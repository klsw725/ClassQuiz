// SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)
//
// SPDX-License-Identifier: MPL-2.0

declare module 'swiper/svelte' {
	import type { ComponentType, SvelteComponent } from 'svelte';

	export const Swiper: ComponentType<SvelteComponent>;
	export const SwiperSlide: ComponentType<SvelteComponent>;
}

declare module 'swiper' {
	const Autoplay: unknown;
	export default Autoplay;
}
