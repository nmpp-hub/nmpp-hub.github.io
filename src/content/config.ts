import { defineCollection, z } from 'astro:content';

const codes = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    path: z.string(),
  }),
});

export const collections = { codes };
