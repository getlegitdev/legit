// @ts-check
import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import react from '@astrojs/react';
import cloudflare from '@astrojs/cloudflare';

// https://astro.build/config
export default defineConfig({
  site: 'https://getlegit.dev',
  output: 'hybrid',
  adapter: cloudflare(),
  integrations: [tailwind(), react()],
});
