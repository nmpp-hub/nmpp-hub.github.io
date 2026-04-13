import { defineCollection, z } from "astro:content";
import { glob } from "astro/loaders";

const codes = defineCollection({
  loader: glob({ pattern: "*.md", base: "./src/content/codes" }),
  schema: z.object({
    title: z.string(),
    path: z.string(),
    gallery: z.array(z.object({
      src: z.string(),
      title: z.string().optional(),
    })).optional(),
  }),
});

const members = defineCollection({
  loader: glob({ pattern: "*.md", base: "./src/content/members" }),
  schema: z.object({
    title: z.string(),
  }),
});

const groups = defineCollection({
  loader: glob({ pattern: "*.md", base: "./src/content/groups" }),
  schema: z.object({
    title: z.string(),
  }),
});

const dissertations = defineCollection({
  loader: glob({ pattern: "*.md", base: "./src/content/dissertations" }),
  schema: z.object({
    title: z.string().optional(),
  }),
});

export const collections = { codes, members, groups, dissertations };
