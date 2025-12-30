
"use client"

import { 
  Video, 
  PlusCircle, 
  Play, 
  Clock, 
  BarChart3, 
  Zap,
  MoreVertical,
  ExternalLink
} from "lucide-react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

const recentDemos = [
  {
    id: "1",
    title: "Onboarding Flow Walkthrough",
    repo: "acme-app-frontend",
    status: "Completed",
    date: "2 hours ago",
    thumbnail: "https://images.unsplash.com/photo-1614332287897-cdc485fa562d?w=400&h=225&fit=crop",
  },
  {
    id: "2",
    title: "Billing Dashboard Demo",
    repo: "acme-billing-service",
    status: "Processing",
    date: "5 hours ago",
    thumbnail: "https://images.unsplash.com/photo-1551288049-bbda3865c170?w=400&h=225&fit=crop",
  },
  {
    id: "3",
    title: "Analytics Feature Highlight",
    repo: "acme-app-frontend",
    status: "Completed",
    date: "Yesterday",
    thumbnail: "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=400&h=225&fit=crop",
  },
]

import { useState, useEffect } from "react"
import { supabase } from "@/lib/supabase"

export default function DashboardPage() {
  const [demos, setDemos] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchDemos() {
      const { data, error } = await supabase
        .from('demos')
        .select('*')
        .order('created_at', { ascending: false })
      
      if (data) setDemos(data)
      setLoading(false)
    }
    fetchDemos()
  }, [])

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
          <p className="text-muted-foreground">
            Manage your autonomous product demos and generation engine.
          </p>
        </div>
            <Link href="/dashboard/new">
              <Button size="lg" className="rounded-full shadow-lg shadow-primary/20">
                <PlusCircle className="mr-2 h-5 w-5" />
                New Demo
              </Button>
            </Link>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Demos</CardTitle>
            <Video className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{demos.length}</div>
            <p className="text-xs text-muted-foreground">Across all projects</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Agents</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">3</div>
            <p className="text-xs text-muted-foreground">Running on 3 repos</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Generation Time</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">14m</div>
            <p className="text-xs text-muted-foreground">Average per demo</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Views</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">1.2k</div>
            <p className="text-xs text-muted-foreground">+180 today</p>
          </CardContent>
        </Card>
      </div>

      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-semibold tracking-tight">Recent Demos</h3>
          <Button variant="ghost" size="sm" className="text-muted-foreground">
            View all
          </Button>
        </div>
          
          {loading ? (
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {[1, 2, 3].map(i => (
                <Card key={i} className="h-[300px] animate-pulse bg-muted" />
              ))}
            </div>
          ) : demos.length === 0 ? (
            <Card className="p-12 text-center border-dashed">
              <div className="flex flex-col items-center gap-2">
                <Video className="h-12 w-12 text-muted-foreground/50" />
                <h4 className="text-lg font-semibold">No demos yet</h4>
                <p className="text-sm text-muted-foreground">Generate your first autonomous demo to see it here.</p>
                <Link href="/dashboard/new" className="mt-4">
                  <Button>Get Started</Button>
                </Link>
              </div>
            </Card>
          ) : (
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {demos.map((demo) => (
                <Link key={demo.id} href={`/dashboard/demo/${demo.id}`}>
                  <Card className="overflow-hidden group hover:border-primary/50 transition-colors h-full">
                    <div className="relative aspect-video overflow-hidden bg-muted">
                      <img 
                        src={demo.thumbnail_url || "https://images.unsplash.com/photo-1614332287897-cdc485fa562d?w=400&h=225&fit=crop"} 
                        alt={demo.title}
                        className="object-cover w-full h-full transition-transform group-hover:scale-105"
                      />
                      <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                        <Button size="icon" variant="secondary" className="rounded-full h-12 w-12 pointer-events-none">
                          <Play className="h-6 w-6 fill-current" />
                        </Button>
                      </div>
                          <div className="absolute top-2 right-2 flex gap-1">
                            {["executing", "recording"].includes(demo.status?.toLowerCase()) && (
                              <Badge variant="default" className="bg-red-500 text-white border-none animate-pulse flex items-center gap-1">
                                <div className="h-1.5 w-1.5 rounded-full bg-white" />
                                LIVE
                              </Badge>
                            )}
                            <Badge variant={demo.status === "Completed" ? "default" : "secondary"} className="backdrop-blur-md bg-background/80 text-foreground border-none capitalize">
                              {demo.status}
                            </Badge>
                          </div>
                        </div>
                        <CardHeader className="p-4 space-y-0">
                          <div className="flex items-start justify-between gap-2">
                            <div className="space-y-1">
                              <CardTitle className="text-base line-clamp-1">{demo.title}</CardTitle>
                              <CardDescription className="flex items-center gap-1.5 text-xs">
                                <ExternalLink className="h-3 w-3" />
                                {demo.repo_url?.split('/').pop()}
                              </CardDescription>
                            </div>
                            <div className="flex items-center gap-1">
                              {["executing", "recording"].includes(demo.status?.toLowerCase()) && (
                                <Link href={`/dashboard/generate?repo=${encodeURIComponent(demo.repo_url)}&prompt=${encodeURIComponent(demo.description || "")}&demo_id=${demo.id}`}>
                                  <Button size="icon" variant="ghost" className="h-8 w-8 text-primary">
                                    <Eye className="h-4 w-4" />
                                  </Button>
                                </Link>
                              )}
                              <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                  <Button variant="ghost" size="icon" className="h-8 w-8" onClick={(e) => e.preventDefault()}>
                                    <MoreVertical className="h-4 w-4" />
                                  </Button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent align="end">
                                  <DropdownMenuItem>Edit Settings</DropdownMenuItem>
                                  <DropdownMenuItem asChild>
                                    <Link href={`/share/${demo.id}`}>
                                      Share Demo
                                    </Link>
                                  </DropdownMenuItem>
                                  <DropdownMenuItem className="text-destructive">Delete</DropdownMenuItem>
                                </DropdownMenuContent>
                              </DropdownMenu>
                            </div>
                          </div>
                        </CardHeader>

                    <CardContent className="px-4 pb-4 pt-0">
                      <p className="text-xs text-muted-foreground">
                        {new Date(demo.created_at).toLocaleDateString()}
                      </p>
                    </CardContent>
                  </Card>
                </Link>
              ))}
            </div>
          )}
      </div>
    </div>
  )
}

