import { createClient } from "@supabase/supabase-js";

/**
 * Server-only client. Uses the anon/publishable key — never import this from
 * a "use client" component, it must stay inside API routes / server code.
 * The `picks` table has a permissive RLS policy because the only thing that
 * can reach it is this server code, gated by proxy.ts's password check.
 */
export function getSupabaseServerClient() {
  const url = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_ANON_KEY;
  if (!url || !key) {
    throw new Error("Missing SUPABASE_URL or SUPABASE_ANON_KEY");
  }
  return createClient(url, key, {
    auth: { persistSession: false },
  });
}
