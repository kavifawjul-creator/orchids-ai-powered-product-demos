import { NextRequest, NextResponse } from "next/server"
import { createClient } from "@supabase/supabase-js"
import { createClient as createServerClient } from "@/lib/supabase/server"

const supabaseAdmin = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
)

export async function POST(request: NextRequest) {
  try {
    const supabase = await createServerClient()
    const { data: { user } } = await supabase.auth.getUser()
    
    if (!user) {
      return NextResponse.json(
        { error: "Unauthorized" },
        { status: 401 }
      )
    }

    const body = await request.json()
    const { repo_url, prompt, title, workspace_id } = body

    if (!repo_url || !prompt) {
      return NextResponse.json(
        { error: "repo_url and prompt are required" },
        { status: 400 }
      )
    }

    const demoTitle = title || prompt.slice(0, 50)
    
    const { data: demo, error: demoError } = await supabaseAdmin
      .from("demos")
      .insert({
        title: demoTitle,
        repo_url,
        description: prompt,
        status: "pending",
        user_id: user.id,
        workspace_id: workspace_id || null
      })
      .select()
      .single()

    if (demoError) {
      console.error("Failed to create demo:", demoError)
      return NextResponse.json(
        { error: "Failed to create demo" },
        { status: 500 }
      )
    }

    const backendUrl = process.env.BACKEND_URL || "http://localhost:8000"
    
    try {
      const backendResponse = await fetch(`${backendUrl}/api/v1/demos/generate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          demo_id: demo.id,
          repo_url,
          prompt,
          title: demoTitle
        }),
        signal: AbortSignal.timeout(10000)
      })

      if (backendResponse.ok) {
        const backendData = await backendResponse.json()
        return NextResponse.json({
          demo_id: demo.id,
          project_id: backendData.project_id,
          status: backendData.status || "pending",
          message: backendData.message || "Demo generation started"
        })
      }
    } catch (backendError) {
      console.warn("Backend not available, demo created in pending state:", backendError)
    }

    return NextResponse.json({
      demo_id: demo.id,
      status: "pending",
      message: "Demo created. Backend processing will start when available."
    })
  } catch (error) {
    console.error("Generate error:", error)
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    )
  }
}
