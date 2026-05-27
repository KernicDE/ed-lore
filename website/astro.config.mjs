// @ts-check
import { defineConfig } from 'astro/config';
import react from '@astrojs/react';

// https://astro.build/config
export default defineConfig({
  integrations: [react()],
  output: 'static',
  site: 'https://kernicde.github.io',
  base: '/ed-lore',
  redirects: {
    '/entity/john/': '/ed-lore/entity/john-ermitage/',
    '/entity/lya/': '/ed-lore/entity/lynda-amanda-ter-holt/',
  },
  build: {
    format: 'directory',
  },
});
