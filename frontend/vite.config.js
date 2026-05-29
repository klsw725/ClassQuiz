// SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)
//
// SPDX-License-Identifier: MPL-2.0

import { sveltekit } from '@sveltejs/kit/vite';

const devApiTarget = process.env.DEV_API_URL ?? 'http://localhost:8000';

/** @type {import("vite").UserConfig} */
const config = {
	plugins: [
		sveltekit(),
		{
			name: 'configure-response-headers',
			configureServer: (server) => {
				server.middlewares.use((_req, _res, next) => {
					/*        res.setHeader("Cross-Origin-Embedder-Policy", "require-corp");
        res.setHeader("Cross-Origin-Opener-Policy", "same-origin");
        res.setHeader("Access-Control-Allow-Origin", "https://ncs3.classquiz.de");*/
					next();
				});
			}
		}
	],
	server: {
		port: 3000,
		proxy: {
			'/api': {
				target: devApiTarget,
				changeOrigin: true
			},
			'/openapi.json': {
				target: devApiTarget,
				changeOrigin: true
			},
			'/socket.io': {
				target: devApiTarget,
				changeOrigin: true,
				ws: true
			}
		}
	},
	preview: {
		port: 3000
	},
	optimizeDeps: {
		include: ['swiper', 'tippy.js']
	},
	build: {
		sourcemap: true
	}

	/* Trying

	ssr: {
		noExternal: ['@ckeditor/*'],
	}

 end trying*/
};

export default config;
