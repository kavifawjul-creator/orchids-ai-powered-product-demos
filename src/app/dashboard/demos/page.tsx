"use client"

import { 
  Video, 
  Play, 
  MoreVertical,
  ExternalLink,
  Globe,
  Lock,
  Trash2,
  Share2,
  Search,
  Filter
} from "lucide-react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useState, useEffect } from "react"
import { createClient } from "@/lib/supabase/client"

export default function DemosListPage() {
  const supabase = createClient()
  const [demos, setDemos] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState("")
  const [statusFilter, setStatusFilter] = useState<string>("all")

  useEffect(() => {
    async function fetchDemos() {
      const { data: { user } } = await supabase.auth.getUser()
      if (!user) return

      let query = supabase
        .from('demos')
        .select('*')
        .order('created_at', { ascending: false })

      if (statusFilter !== "all") {
        query = query.eq('status', statusFilter)
      }

      const { data } = await query
      setDemos(data || [])
      setLoading(false)
    }
    fetchDemos()
  }, [statusFilter, supabase])

  const filteredDemos = demos.filter(demo => 
    demo.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    demo.repo_url?.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const handleDelete = async (demoId: string) => {
    await supabase.from('demos').delete().eq('id', demoId)
    setDemos(demos.filter(d => d.id !== demoId))
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">All Demos</h2>
          <p className="text-muted-foreground">
            Browse and manage all your product demos
          </p>
        </div>
      </div>

      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search demos..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[180px]">
            <Filter className="h-4 w-4 mr-2" />
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            <SelectItem value="completed">Completed</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="executing">Executing</SelectItem>
            <SelectItem value="error">Error</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {loading ? (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {[1, 2, 3, 4, 5, 6].map(i => (
            <Card key={i} className="h-[280px] animate-pulse bg-muted" />
          ))}
        </div>
      ) : filteredDemos.length === 0 ? (
        <Card className="p-12 text-center border-dashed">
          <div className="flex flex-col items-center gap-2">
            <Video className="h-12 w-12 text-muted-foreground/50" />
            <h4 className="text-lg font-semibold">No demos found</h4>
            <p className="text-sm text-muted-foreground">
              {searchQuery ? "Try adjusting your search" : "Generate your first demo to see it here."}
            </p>
          </div>
        </Card>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {filteredDemos.map((demo) => (
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
                  <div className="absolute top-2 left-2">
                    {demo.is_public ? (
                      <Badge variant="outline" className="bg-green-500/20 text-green-600 border-green-500/30 flex items-center gap-1">
                        <Globe className="h-3 w-3" />
                        Public
                      </Badge>
                    ) : (
                      <Badge variant="outline" className="bg-gray-500/20 text-gray-600 border-gray-500/30 flex items-center gap-1">
                        <Lock className="h-3 w-3" />
                        Private
                      </Badge>
                    )}
                  </div>
                  <div className="absolute top-2 right-2">
                    <Badge variant={demo.status === "completed" ? "default" : "secondary"} className="backdrop-blur-md bg-background/80 text-foreground border-none capitalize">
                      {demo.status}
                    </Badge>
                  </div>
                </div>
                <CardHeader className="p-4 space-y-0">
                  <div className="flex items-start justify-between gap-2">
                    <div className="space-y-1 min-w-0">
                      <CardTitle className="text-base line-clamp-1">{demo.title}</CardTitle>
                      <CardDescription className="flex items-center gap-1.5 text-xs">
                        <ExternalLink className="h-3 w-3 shrink-0" />
                        <span className="truncate">{demo.repo_url?.split('/').pop()}</span>
                      </CardDescription>
                    </div>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon" className="h-8 w-8 shrink-0" onClick={(e) => e.preventDefault()}>
                          <MoreVertical className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={(e) => { 
                          e.preventDefault()
                          navigator.clipboard.writeText(`${window.location.origin}/share/${demo.id}`)
                        }}>
                          <Share2 className="h-4 w-4 mr-2" />
                          Copy Share Link
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem 
                          className="text-destructive"
                          onClick={(e) => { e.preventDefault(); handleDelete(demo.id) }}
                        >
                          <Trash2 className="h-4 w-4 mr-2" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
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
  )
}
