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
      .select("*")
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

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const body = await request.json()

    const { data: demo, error } = await supabase
      .from("demos")
      .update({ ...body, updated_at: new Date().toISOString() })
      .eq("id", id)
      .select()
      .single()

    if (error) {
      return NextResponse.json(
        { error: "Failed to update demo" },
        { status: 500 }
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

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params

    await supabase.from("clips").delete().eq("demo_id", id)
    
    const { error } = await supabase
      .from("demos")
      .delete()
      .eq("id", id)

    if (error) {
      return NextResponse.json(
        { error: "Failed to delete demo" },
        { status: 500 }
      )
    }

    return NextResponse.json({ message: "Demo deleted" })
  } catch (error) {
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    )
  }
}
