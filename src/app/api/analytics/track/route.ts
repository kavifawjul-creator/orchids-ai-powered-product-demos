import { NextRequest, NextResponse } from "next/server";
import { supabase } from "@/lib/supabase";

export async function POST(req: NextRequest) {
  try {
    const { demo_id, event_type, metadata } = await req.json();

    if (!demo_id || !event_type) {
      return NextResponse.json({ error: "Missing required fields" }, { status: 400 });
    }

    const { error } = await supabase.from("analytics").insert({
      demo_id,
      event_type,
      metadata: metadata || {},
      user_agent: req.headers.get("user-agent") || "unknown",
      viewer_ip: req.headers.get("x-forwarded-for") || "unknown"
    });

    if (error) throw error;

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Analytics error:", error);
    return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
  }
}
