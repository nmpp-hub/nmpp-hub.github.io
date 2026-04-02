import { defineCollection, z } from 'astro:content';

const codes = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    path: z.string(),
  }),
});

const members = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
  }),
});

const groups = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
  }),
});

export const collections = { codes, members, groups };
