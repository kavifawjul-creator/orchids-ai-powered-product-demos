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

    const { data: project, error: projectError } = await supabase
      .from("projects")
      .insert({
        repo_url,
        title: repoName,
        status: "pending",
        metadata: { prompt }
      })
      .select()
      .single()

    if (projectError) {
      console.error("Project creation error:", projectError)
    }

    const { data: demo, error: demoError } = await supabase
      .from("demos")
      .insert({
        title: demoTitle,
        repo_url,
        description: prompt,
        status: "pending",
        project_id: project?.id
      })
      .select()
      .single()

    if (demoError) {
      return NextResponse.json(
        { error: "Failed to create demo" },
        { status: 500 }
      )
    }

    return NextResponse.json({
      demo_id: demo.id,
      project_id: project?.id,
      status: "pending",
      message: "Demo generation started"
    })
  } catch (error) {
    console.error("Generate error:", error)
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    )
  }
}
