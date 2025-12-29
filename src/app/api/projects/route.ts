import { NextRequest, NextResponse } from "next/server"
import { createClient } from "@supabase/supabase-js"

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
)

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { repo_url, title } = body

    if (!repo_url) {
      return NextResponse.json(
        { error: "repo_url is required" },
        { status: 400 }
      )
    }

    const repoName = title || repo_url.split("/").pop()?.replace(".git", "") || "Project"

    const { data: project, error } = await supabase
      .from("projects")
      .insert({
        repo_url,
        title: repoName,
        status: "pending"
      })
      .select()
      .single()

    if (error) {
      return NextResponse.json(
        { error: "Failed to create project" },
        { status: 500 }
      )
    }

    return NextResponse.json({
      id: project.id,
      repo_url: project.repo_url,
      title: project.title,
      status: project.status,
      created_at: project.created_at
    })
  } catch (error) {
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    )
  }
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const limit = parseInt(searchParams.get("limit") || "50")
    const offset = parseInt(searchParams.get("offset") || "0")

    const { data: projects, error } = await supabase
      .from("projects")
      .select("*")
      .order("created_at", { ascending: false })
      .range(offset, offset + limit - 1)

    if (error) {
      return NextResponse.json(
        { error: "Failed to fetch projects" },
        { status: 500 }
      )
    }

    return NextResponse.json({ projects: projects || [] })
  } catch (error) {
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    )
  }
}
