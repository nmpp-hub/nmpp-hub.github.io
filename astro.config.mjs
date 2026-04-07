
import { defineConfig } from "astro/config";
import rehypeRaw from "rehype-raw";
import react from "@astrojs/react";

export default defineConfig({
  site: "https://nmpp-hub.github.io",
  trailingSlash: "always",
  integrations: [react()],
  markdown: {
    rehypePlugins: [rehypeRaw],
  },
});
