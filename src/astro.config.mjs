import { defineConfig } from 'astro/config';

// https://astro.build/config
export default defineConfig({
  site: 'https://humancronadmin.github.io',
  base: '/discontinued-cosmetics',
  trailingSlash: 'ignore',
  build: {
    format: 'directory',
  },
});
