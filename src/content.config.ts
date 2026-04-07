import { defineCollection, z } from "astro:content";

const codes = defineCollection({
  schema: z.object({
    title: z.string(),
    path: z.string(),
  }),
  loader: ({ id, data }) => {
    return {
      ...data,
      slug: id.replace(/\.md$/, ""),
    };
  },
});

const members = defineCollection({
  schema: z.object({
    title: z.string(),
  }),
});

const groups = defineCollection({
  schema: z.object({
    title: z.string(),
  }),
  loader: ({ id, data }) => {
    return {
      ...data,
      slug: id.replace(/\.md$/, ""),
    };
  },
});

const dissertations = defineCollection({
  schema: z.object({
    title: z.string().optional(),
  }),
});

export const collections = { codes, members, groups, dissertations };
