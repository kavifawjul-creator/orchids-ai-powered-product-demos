import { NextRequest, NextResponse } from "next/server"
import { createClient } from "@supabase/supabase-js"

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
)

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { repo_url, prompt, title } = body

    if (!repo_url || !prompt) {
      return NextResponse.json(
        { error: "repo_url and prompt are required" },
        { status: 400 }
      )
    }

    const repoName = repo_url.split("/").pop()?.replace(".git", "") || "Demo"
    const demoTitle = title || prompt.slice(0, 50)

    // Call Python backend to start generation
    const backendUrl = process.env.BACKEND_URL || "http://localhost:8000"
    const backendResponse = await fetch(`${backendUrl}/api/v1/demos/generate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        repo_url,
        prompt,
        title: demoTitle
      }),
    })

    if (!backendResponse.ok) {
      const errorData = await backendResponse.json()
      console.error("Backend error:", errorData)
      return NextResponse.json(
        { error: errorData.detail || "Failed to trigger generation in backend" },
        { status: backendResponse.status }
      )
    }

    const backendData = await backendResponse.json()

    return NextResponse.json({
      demo_id: backendData.demo_id,
      project_id: backendData.project_id,
      status: backendData.status,
      message: backendData.message
    })
  } catch (error) {
    console.error("Generate error:", error)
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    )
  }
}
