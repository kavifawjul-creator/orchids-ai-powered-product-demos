
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

export default function DashboardPage() {
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
            <div className="text-2xl font-bold">12</div>
            <p className="text-xs text-muted-foreground">+2 from last month</p>
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
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {recentDemos.map((demo) => (
            <Card key={demo.id} className="overflow-hidden group hover:border-primary/50 transition-colors">
              <div className="relative aspect-video overflow-hidden bg-muted">
                <img 
                  src={demo.thumbnail} 
                  alt={demo.title}
                  className="object-cover w-full h-full transition-transform group-hover:scale-105"
                />
                <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                  <Button size="icon" variant="secondary" className="rounded-full h-12 w-12">
                    <Play className="h-6 w-6 fill-current" />
                  </Button>
                </div>
                <div className="absolute top-2 right-2">
                  <Badge variant={demo.status === "Completed" ? "default" : "secondary"} className="backdrop-blur-md bg-background/80 text-foreground border-none">
                    {demo.status}
                  </Badge>
                </div>
              </div>
              <CardHeader className="p-4 space-y-0">
                <div className="flex items-start justify-between gap-2">
                  <div className="space-y-1">
                    <CardTitle className="text-base line-clamp-1">{demo.title}</CardTitle>
                    <CardDescription className="flex items-center gap-1.5">
                      <ExternalLink className="h-3 w-3" />
                      {demo.repo}
                    </CardDescription>
                  </div>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon" className="h-8 w-8">
                        <MoreVertical className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem>Edit Settings</DropdownMenuItem>
                      <DropdownMenuItem>Share Demo</DropdownMenuItem>
                      <DropdownMenuItem className="text-destructive">Delete</DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </CardHeader>
              <CardContent className="px-4 pb-4 pt-0">
                <p className="text-xs text-muted-foreground">{demo.date}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  )
}
