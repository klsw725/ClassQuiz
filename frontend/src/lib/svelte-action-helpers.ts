// SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)
//
// SPDX-License-Identifier: MPL-2.0

import type { Action } from 'svelte/action';

export const htmlElementAction = <Parameter>(
	action: Action<HTMLElement, Parameter>
): Action<Element, Parameter> => action as Action<Element, Parameter>;
