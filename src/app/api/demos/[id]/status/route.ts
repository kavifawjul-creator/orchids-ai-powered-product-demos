import { NextRequest, NextResponse } from "next/server"
import { createClient } from "@supabase/supabase-js"

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
)

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params

    const { data: demo, error } = await supabase
      .from("demos")
      .select("id, status, title, updated_at, description")
      .eq("id", id)
      .single()

    if (error || !demo) {
      return NextResponse.json(
        { error: "Demo not found" },
        { status: 404 }
      )
    }

    return NextResponse.json(demo)
  } catch (error) {
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    )
  }
}
