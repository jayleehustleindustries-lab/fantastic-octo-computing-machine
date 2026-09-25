import { NextRequest, NextResponse } from "next/server";
import { getSupabaseServerClient } from "@/lib/supabase";

export async function GET() {
  const supabase = getSupabaseServerClient();
  const { data, error } = await supabase
    .from("picks")
    .select("*")
    .order("event_date", { ascending: false })
    .order("created_at", { ascending: false });

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
  return NextResponse.json({ picks: data });
}

export async function POST(req: NextRequest) {
  const body = await req.json();

  const required = [
    "event_date",
    "sport",
    "matchup",
    "platform",
    "market",
    "side",
    "odds_format",
    "odds_value",
    "stake",
    "potential_payout",
  ];
  for (const field of required) {
    if (body[field] === undefined || body[field] === null || body[field] === "") {
      return NextResponse.json({ error: `Missing field: ${field}` }, { status: 400 });
    }
  }

  const supabase = getSupabaseServerClient();
  const { data, error } = await supabase
    .from("picks")
    .insert({
      event_date: body.event_date,
      sport: body.sport,
      matchup: body.matchup,
      platform: body.platform,
      player: body.player || null,
      market: body.market,
      line: body.line === "" || body.line === undefined ? null : Number(body.line),
      side: body.side,
      odds_format: body.odds_format,
      odds_value: Number(body.odds_value),
      parlay_id: body.parlay_id || null,
      legs_in_parlay: body.legs_in_parlay ? Number(body.legs_in_parlay) : 1,
      stake: Number(body.stake),
      potential_payout: Number(body.potential_payout),
      notes: body.notes || null,
    })
    .select()
    .single();

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
  return NextResponse.json({ pick: data }, { status: 201 });
}
