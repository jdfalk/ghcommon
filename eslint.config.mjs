// @ts-check

import eslint from '@eslint/js';
import { defineConfig } from 'eslint/config';
import tseslint from 'typescript-eslint';
import globals from 'globals';

export default defineConfig(
  {
    ignores: [
      '.github/test-files/**',
      'testdata/**',
      '.commitlintrc.js',
      '.vscode/**',
      'dependency-analysis/**',
      'logs/**',
    ],
  },
  eslint.configs.recommended,
  tseslint.configs.recommended,
  {
    languageOptions: {
      globals: {
        ...globals.node,
      },
    },
  }
);
