import { z } from "zod"

const envSchema = z.object({
  NEXT_PUBLIC_SUPABASE_URL: z.string().url(),
  NEXT_PUBLIC_SUPABASE_ANON_KEY: z.string().min(1),
  NEXT_PUBLIC_APP_URL: z.string().url().optional().default("http://localhost:3000"),
  BACKEND_URL: z.string().url().optional().default("http://localhost:8000"),
})

// Safe parse to avoid crashing during build if some vars are missing but not used
const parsed = envSchema.safeParse(process.env)

if (!parsed.success) {
  console.error("❌ Invalid environment variables:", parsed.error.format())
  // Only throw in production or if you want to be strict
  // throw new Error("Invalid environment variables")
}

export const env = parsed.success ? parsed.data : process.env as unknown as z.infer<typeof envSchema>
