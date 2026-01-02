
"use client"

import * as React from "react"
import { useRouter } from "next/navigation"
import { 
  GitBranch, 
  Terminal, 
  ArrowRight, 
  Sparkles, 
  Zap, 
  ShieldCheck,
  Layout,
  MessageSquare,
  MousePointer2,
  ChevronRight
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Label } from "@/components/ui/label"
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs"

const templates = [
  {
    title: "Feature Walkthrough",
    description: "Deep dive into a specific feature or flow.",
    icon: MousePointer2,
    prompt: "Create a detailed walkthrough of our new analytics dashboard, highlighting the date range picker and the export functionality."
  },
  {
    title: "Onboarding Guide",
    description: "Guide new users through their first steps.",
    icon: Layout,
    prompt: "Show a new user how to sign up, create their first project, and invite their team members."
  },
  {
    title: "Release Highlight",
    description: "Showcase what's new in your latest update.",
    icon: Sparkles,
    prompt: "Demonstrate the top 3 features in our v2.0 release: dark mode, nested folders, and the global search."
  }
]

export default function NewDemoPage() {
  const router = useRouter()
  const [repoUrl, setRepoUrl] = React.useState("")
  const [prompt, setPrompt] = React.useState("")
  const [isGenerating, setIsGenerating] = React.useState(false)

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsGenerating(true)
    
    try {
      const response = await fetch("/api/demos/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          repo_url: repoUrl,
          prompt: prompt,
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || "Failed to start generation")
      }

      router.push(`/dashboard/generate?demo_id=${data.demo_id}&repo=${encodeURIComponent(repoUrl)}&prompt=${encodeURIComponent(prompt)}`)
    } catch (error) {
      console.error("Generation error:", error)
      setIsGenerating(false)
      // You might want to show a toast here
    }
  }

  const applyTemplate = (templatePrompt: string) => {
    setPrompt(templatePrompt)
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-12">
      <div className="space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">Create New Demo</h2>
        <p className="text-muted-foreground text-lg">
          Point AutoVidAI to your repository and tell us what you want to showcase.
        </p>
      </div>

      <div className="grid gap-8 md:grid-cols-3">
        <div className="md:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Configuration</CardTitle>
              <CardDescription>
                Your application source and demo instructions.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleGenerate} className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="repo">Repository URL</Label>
                  <div className="relative">
                    <GitBranch className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input 
                      id="repo" 
                      placeholder="https://github.com/acme/app" 
                      className="pl-10 h-12"
                      value={repoUrl}
                      onChange={(e) => setRepoUrl(e.target.value)}
                      required
                    />
                  </div>
                  <p className="text-[10px] text-muted-foreground">Supports GitHub, GitLab, and Bitbucket public or private repos.</p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="prompt">What should the AI demonstrate?</Label>
                  <div className="relative">
                    <MessageSquare className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Textarea 
                      id="prompt" 
                      placeholder="Describe the flow, features, or specific interactions..." 
                      className="min-h-[150px] pl-10 pt-3"
                      value={prompt}
                      onChange={(e) => setPrompt(e.target.value)}
                      required
                    />
                  </div>
                </div>

                <div className="pt-2">
                  <Button 
                    type="submit" 
                    size="lg" 
                    className="w-full h-14 rounded-xl text-lg font-semibold shadow-xl shadow-primary/20"
                    disabled={isGenerating}
                  >
                    {isGenerating ? (
                      <span className="flex items-center gap-2">
                        <Zap className="h-5 w-5 animate-pulse text-yellow-400" />
                        Initializing Engine...
                      </span>
                    ) : (
                      <span className="flex items-center gap-2">
                        Generate Autonomous Demo
                        <ArrowRight className="h-5 w-5" />
                      </span>
                    )}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>

          <div className="grid gap-4 md:grid-cols-2">
            <Card className="bg-muted/30 border-dashed">
              <CardContent className="pt-6">
                <div className="flex items-center gap-2 mb-2">
                  <ShieldCheck className="h-4 w-4 text-primary" />
                  <span className="text-sm font-semibold">Security First</span>
                </div>
                <p className="text-xs text-muted-foreground">
                  We run your code in an isolated, temporary environment. No data persists after generation.
                </p>
              </CardContent>
            </Card>
            <Card className="bg-muted/30 border-dashed">
              <CardContent className="pt-6">
                <div className="flex items-center gap-2 mb-2">
                  <Terminal className="h-4 w-4 text-primary" />
                  <span className="text-sm font-semibold">Automatic Detection</span>
                </div>
                <p className="text-xs text-muted-foreground">
                  AutoVidAI automatically identifies framework, routes, and key components in your codebase.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>

        <div className="space-y-6">
          <div className="font-semibold text-sm flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-primary" />
            Quick Templates
          </div>
          <div className="space-y-4">
            {templates.map((template, i) => (
              <button 
                key={i}
                onClick={() => applyTemplate(template.prompt)}
                className="w-full text-left group"
              >
                <Card className="hover:border-primary/50 transition-colors group-hover:shadow-md">
                  <CardHeader className="p-4">
                    <div className="flex items-center gap-3">
                      <div className="p-2 rounded-lg bg-primary/10 text-primary group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
                        <template.icon className="h-4 w-4" />
                      </div>
                      <div>
                        <CardTitle className="text-sm">{template.title}</CardTitle>
                        <CardDescription className="text-[10px] line-clamp-1">{template.description}</CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                </Card>
              </button>
            ))}
          </div>

          <Card className="bg-primary/5 border-primary/20">
            <CardHeader className="p-4">
              <CardTitle className="text-sm">Pro Tip</CardTitle>
              <CardDescription className="text-xs text-foreground/70">
                The more specific your prompt, the better the AI can focus on the right features. Mention specific component names if you want precise targeting.
              </CardDescription>
            </CardHeader>
          </Card>
        </div>
      </div>
    </div>
  )
}
