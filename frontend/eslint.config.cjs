// SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)
//
// SPDX-License-Identifier: MPL-2.0

const { defineConfig, globalIgnores } = require('eslint/config');

const tsParser = require('@typescript-eslint/parser');
const typescriptEslint = require('@typescript-eslint/eslint-plugin');
const globals = require('globals');
const js = require('@eslint/js');
const svelte = require('eslint-plugin-svelte');

module.exports = defineConfig([
	js.configs.recommended,
	svelte.configs.recommended,
	globalIgnores(['**/*.cjs', 'src/app.html', '.svelte-kit/**', 'build/**']),
	{
		languageOptions: {
			sourceType: 'module',
			ecmaVersion: 2020,

			globals: {
				...globals.browser,
				...globals.node
			}
		}
	},
	{
		files: ['**/*.js'],
		rules: {
			'no-unused-vars': [
				'error',
				{
					argsIgnorePattern: '^_.*'
				}
			]
		}
	},
	{
		files: ['**/*.{ts,tsx}'],
		languageOptions: {
			parser: tsParser
		},

		plugins: {
			'@typescript-eslint': typescriptEslint
		},

		rules: {
			'no-undef': 'off',
			'no-unused-vars': 'off',

			'@typescript-eslint/no-unused-vars': [
				'error',
				{
					argsIgnorePattern: '^_.*'
				}
			]
		}
	},
	{
		files: ['**/*.d.ts'],
		languageOptions: {
			parser: tsParser
		},

		plugins: {
			'@typescript-eslint': typescriptEslint
		},

		rules: {
			'no-undef': 'off',
			'no-unused-vars': 'off',
			'@typescript-eslint/no-unused-vars': 'off'
		}
	},
	{
		files: ['**/*.svelte'],
		languageOptions: {
			parserOptions: {
				parser: tsParser,
				extraFileExtensions: ['.svelte']
			}
		},

		plugins: {
			'@typescript-eslint': typescriptEslint
		},

		rules: {
			'no-undef': 'off',
			'no-unused-vars': [
				'error',
				{
					argsIgnorePattern: '^_.*'
				}
			],
			'@typescript-eslint/no-unused-vars': [
				'error',
				{
					argsIgnorePattern: '^_.*'
				}
			],
			'svelte/no-navigation-without-resolve': 'warn',
			'svelte/no-at-html-tags': 'warn',
			'svelte/require-each-key': 'warn'
		}
	},
	{
		files: ['**/*.svelte', '**/*.ts', '**/*.js'],

		rules: {
			'a11y-click-events-have-key-events': 'off'
		}
	}
]);
