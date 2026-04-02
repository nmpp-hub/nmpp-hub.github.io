import { defineConfig } from 'astro/config';
import rehypeRaw from 'rehype-raw';

export default defineConfig({
  site: 'https://nmpp-hub.github.io',
  trailingSlash: 'always',
  markdown: {
    rehypePlugins: [rehypeRaw],
  },
});
