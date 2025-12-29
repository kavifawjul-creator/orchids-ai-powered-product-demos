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

    const { data: clips, error } = await supabase
      .from("clips")
      .select("*")
      .eq("demo_id", id)
      .order("order_index")

    if (error) {
      return NextResponse.json(
        { error: "Failed to fetch clips" },
        { status: 500 }
      )
    }

    return NextResponse.json({ clips: clips || [] })
  } catch (error) {
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    )
  }
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const body = await request.json()

    const { data: clip, error } = await supabase
      .from("clips")
      .insert({
        demo_id: id,
        ...body
      })
      .select()
      .single()

    if (error) {
      return NextResponse.json(
        { error: "Failed to create clip" },
        { status: 500 }
      )
    }

    return NextResponse.json(clip)
  } catch (error) {
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    )
  }
}
