import { z, defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';

const products = defineCollection({
  loader: glob({ pattern: '**/[^_]*.md', base: './src/content/products' }),
  schema: z.object({
    brand: z.string(),
    product_name: z.string(),
    slug: z.string(),
    category: z.enum([
      'lipstick',
      'eyeshadow',
      'foundation',
      'blush',
      'mascara',
      'fragrance',
      'skincare',
    ]),
    launched_year: z.number().int().nullable().optional(),
    discontinued_year: z.number().int().nullable().optional(),
    original_price_usd: z.number().nullable().optional(),
    sold_history: z
      .array(
        z.object({
          date: z.string(),
          platform: z.string(),
          price_usd: z.number(),
          url: z.string().url(),
        })
      )
      .default([]),
    successor_product: z
      .object({
        brand: z.string(),
        product: z.string(),
      })
      .nullable()
      .optional(),
    dupes: z
      .array(
        z.object({
          brand: z.string(),
          product: z.string(),
        })
      )
      .default([]),
    reddit_mentions: z.array(z.string().url()).default([]),
    sources: z.array(z.string().url()).default([]),
    draft: z.boolean().default(true),
    image_url: z.string().url().nullable().optional(),
    description: z.string().optional(),
  }),
});

export const collections = { products };
