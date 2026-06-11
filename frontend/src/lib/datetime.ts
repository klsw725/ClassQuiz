// SPDX-FileCopyrightText: 2026 ClassQuiz contributors
//
// SPDX-License-Identifier: MPL-2.0

const TIMEZONE_SUFFIX = /(?:Z|[+-]\d{2}:?\d{2})$/i;

export const parseApiDateTime = (timestamp: string): Date => {
	const normalizedTimestamp = TIMEZONE_SUFFIX.test(timestamp) ? timestamp : `${timestamp}Z`;
	return new Date(normalizedTimestamp);
};

export const formatApiDateTime = (timestamp: string): string =>
	parseApiDateTime(timestamp).toLocaleString();
