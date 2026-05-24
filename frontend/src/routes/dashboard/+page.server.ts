// SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)
//
// SPDX-License-Identifier: MPL-2.0

import { error, redirect } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';

const apiUrl = process.env.API_URL ?? '';

const fetchDashboardJson = async <T>(
	fetch: typeof globalThis.fetch,
	cookie: string,
	path: string
): Promise<T> => {
	let res: Response;
	try {
		res = await fetch(`${apiUrl}${path}`, {
			headers: {
				cookie
			}
		});
	} catch {
		error(502, 'Dashboard API unavailable');
	}

	if (res.status === 401) {
		redirect(302, '/account/login?returnTo=/dashboard');
	}

	if (!res.ok) {
		error(res.status, 'Failed to load dashboard data');
	}

	return (await res.json()) as T;
};

export const load: PageServerLoad = async ({ fetch, parent, request }) => {
	const { email } = await parent();
	if (!email) {
		redirect(302, '/account/login?returnTo=/dashboard');
	}

	const cookie = request.headers.get('cookie') ?? '';
	const [quizzes, quiztivities, live_games] = await Promise.all([
		fetchDashboardJson(fetch, cookie, '/api/v1/quiz/list?page_size=100'),
		fetchDashboardJson(fetch, cookie, '/api/v1/quiztivity/'),
		fetchDashboardJson(fetch, cookie, '/api/v1/remote/live_games')
	]);

	return {
		email,
		quizzes,
		quiztivities,
		live_games
	};
};
