// SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)
//
// SPDX-License-Identifier: MPL-2.0

import { reach } from 'yup';

type SyncValidSchema = {
	isValidSync: (value: unknown) => boolean;
};

export const isSchemaPathValid = (schema: object, path: string, value: unknown): boolean =>
	(reach(schema as never, path) as SyncValidSchema).isValidSync(value);
