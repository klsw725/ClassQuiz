<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import { Swiper, SwiperSlide } from 'swiper/svelte';
	import Autoplay from 'swiper';
	import 'swiper/css';
	// import 'swiper/css/autoplay';

	const testimotionals = [
		{
			quote: `#ClassQuiz: An open source quiz platform (like Kahoot!) made by @Mawoka
 and written mostly in #svelte and #python.
I like it and would use it for my house parties next time!`,
			name: 'Deekshith Allamaneni',
			source: 'https://twitter.com/adeekshith/status/1514973178438766596'
		}
	];
</script>

<div class="lg:grid lg:grid-cols-3">
	<div class="lg:col-start-2">
		<Swiper
			centeredSlides={true}
			modules={[Autoplay]}
			autoplay={{
				delay: 3500,
				disableOnInteraction: false
			}}
			loop={true}
		>
			{#each testimotionals as testi}
				<SwiperSlide>
					<div class="flex justify-center">
						<div class="cq-card max-w-3xl p-4 text-cq-text">
							<div class="mb-2">
								<div class="h-3 text-left text-3xl text-cq-muted">“</div>
								<p class="px-4 text-center font-medium text-cq-text">
									{@html testi.quote}
								</p>
								<div class="h-3 text-right text-3xl text-cq-muted">”</div>
								<div class="text-center">
									<h5 class="font-bold text-cq-text">{testi.name}</h5>
									<a class="link-hover text-sm text-cq-muted" href={testi.source}>Source</a>
								</div>
							</div>
						</div>
					</div>
				</SwiperSlide>
			{/each}
		</Swiper>
	</div>
</div>
