"use client"

import { 
  Video, 
  PlusCircle, 
  Play, 
  Clock, 
  BarChart3, 
  Zap,
  MoreVertical,
  ExternalLink,
  Eye,
  ChevronDown,
  Users,
  Globe,
  Lock,
  Trash2,
  Share2
} from "lucide-react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Switch } from "@/components/ui/switch"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
  DropdownMenuLabel,
} from "@/components/ui/dropdown-menu"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"

import { useState, useEffect } from "react"
import { createClient } from "@/lib/supabase/client"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { toast } from "sonner"

export default function DashboardPage() {
  const supabase = createClient()
  const router = useRouter()
  const [demos, setDemos] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState({ views: 0, activeAgents: 0, avgTime: "14m" })
  const [workspaces, setWorkspaces] = useState<any[]>([])
  const [currentWorkspace, setCurrentWorkspace] = useState<any>(null)
  const [settingsDemo, setSettingsDemo] = useState<any>(null)
  const [deleteDemo, setDeleteDemo] = useState<any>(null)
  const [shareDemo, setShareDemo] = useState<any>(null)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    async function fetchData() {
      const { data: { user } } = await supabase.auth.getUser()
      if (!user) return

      const { data: wsData } = await supabase
        .from('workspaces')
        .select('*')
        .eq('owner_id', user.id)

      if (wsData && wsData.length > 0) {
        setWorkspaces(wsData)
        if (!currentWorkspace) setCurrentWorkspace(wsData[0])
      } else {
        const { data: newWs } = await supabase.from('workspaces').insert({
          name: "Personal Workspace",
          owner_id: user.id,
          slug: `workspace-${user.id.slice(0, 8)}`
        }).select().single()
        if (newWs) {
          setWorkspaces([newWs])
          setCurrentWorkspace(newWs)
        }
      }

      let query = supabase
        .from('demos')
        .select('*')
        .order('created_at', { ascending: false })

      if (currentWorkspace?.id) {
        query = query.eq('workspace_id', currentWorkspace.id)
      }
      
      const { data: demosData } = await query
      
      if (demosData) {
        setDemos(demosData)
        const active = demosData.filter(d => ["executing", "recording", "planning", "building"].includes(d.status?.toLowerCase())).length
        
        const { count: viewsCount } = await supabase
          .from('analytics')
          .select('id', { count: 'exact' })
          .eq('event_type', 'view')
          .limit(0)

        setStats({
          views: viewsCount || 0,
          activeAgents: active,
          avgTime: "12m"
        })
      }
      setLoading(false)
    }
    fetchData()
  }, [currentWorkspace?.id, supabase])

  const handleTogglePublic = async (demoId: string, isPublic: boolean) => {
    await supabase
      .from('demos')
      .update({ is_public: isPublic })
      .eq('id', demoId)

    setDemos(demos.map(d => d.id === demoId ? { ...d, is_public: isPublic } : d))
    if (settingsDemo?.id === demoId) {
      setSettingsDemo({ ...settingsDemo, is_public: isPublic })
    }
    toast.success(isPublic ? "Demo is now public" : "Demo is now private")
  }

  const handleDeleteDemo = async () => {
    if (!deleteDemo) return
    await supabase.from('demos').delete().eq('id', deleteDemo.id)
    setDemos(demos.filter(d => d.id !== deleteDemo.id))
    setDeleteDemo(null)
    toast.success("Demo deleted successfully")
  }

  const handleCopyShareLink = () => {
    if (!shareDemo) return
    const shareUrl = `${window.location.origin}/share/${shareDemo.id}`
    navigator.clipboard.writeText(shareUrl)
    setCopied(true)
    toast.success("Link copied to clipboard")
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-4">
          <div>
            <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
            <p className="text-muted-foreground">
              Manage your autonomous product demos.
            </p>
          </div>
          <div className="h-10 w-[1px] bg-border mx-2 hidden md:block" />
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" className="rounded-full gap-2 px-4 border-primary/20 bg-primary/5 hover:bg-primary/10">
                <Users size={16} />
                <span className="font-semibold">{currentWorkspace?.name || "Loading..."}</span>
                <ChevronDown size={14} className="opacity-50" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start" className="w-56">
              <DropdownMenuLabel>Switch Workspace</DropdownMenuLabel>
              <DropdownMenuSeparator />
              {workspaces.map(ws => (
                <DropdownMenuItem key={ws.id} onClick={() => setCurrentWorkspace(ws)} className="flex items-center justify-between">
                  {ws.name}
                  {currentWorkspace?.id === ws.id && <div className="h-2 w-2 rounded-full bg-primary" />}
                </DropdownMenuItem>
              ))}
              <DropdownMenuSeparator />
              <DropdownMenuItem className="text-primary font-medium">
                <PlusCircle size={14} className="mr-2" /> Create New Workspace
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
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
            <div className="text-2xl font-bold">{stats.activeAgents}</div>
            <p className="text-xs text-muted-foreground">Running live sessions</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Generation Time</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.avgTime}</div>
            <p className="text-xs text-muted-foreground">Average per demo</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Views</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.views}</div>
            <p className="text-xs text-muted-foreground">Across all demos</p>
          </CardContent>
        </Card>
      </div>

      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-semibold tracking-tight">Recent Demos</h3>
            <Button variant="ghost" size="sm" className="text-muted-foreground" onClick={() => router.push('/dashboard/demos')}>
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
                              <Button size="icon" variant="ghost" className="h-8 w-8 text-primary" onClick={(e) => e.stopPropagation()}>
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
                              <DropdownMenuItem onClick={(e) => { e.preventDefault(); setSettingsDemo(demo); }}>
                                Privacy Settings
                              </DropdownMenuItem>
                              <DropdownMenuItem onClick={(e) => { e.preventDefault(); setShareDemo(demo); }}>
                                <Share2 className="h-4 w-4 mr-2" />
                                Share Demo
                              </DropdownMenuItem>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem 
                                className="text-destructive"
                                onClick={(e) => { e.preventDefault(); setDeleteDemo(demo); }}
                              >
                                <Trash2 className="h-4 w-4 mr-2" />
                                Delete
                              </DropdownMenuItem>
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

      <Dialog open={!!settingsDemo} onOpenChange={() => setSettingsDemo(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Privacy Settings</DialogTitle>
            <DialogDescription>
              Control who can view this demo
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 rounded-lg border">
              <div className="flex items-center gap-3">
                {settingsDemo?.is_public ? (
                  <Globe className="h-5 w-5 text-green-600" />
                ) : (
                  <Lock className="h-5 w-5 text-gray-600" />
                )}
                <div>
                  <p className="font-medium">
                    {settingsDemo?.is_public ? "Public" : "Private"}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {settingsDemo?.is_public 
                      ? "Anyone with the link can view" 
                      : "Only you can view this demo"}
                  </p>
                </div>
              </div>
              <Switch
                checked={settingsDemo?.is_public || false}
                onCheckedChange={(checked) => handleTogglePublic(settingsDemo?.id, checked)}
              />
            </div>
            {settingsDemo?.is_public && (
              <div className="space-y-2">
                <Label>Share Link</Label>
                <div className="flex gap-2">
                  <Input
                    readOnly
                    value={`${typeof window !== 'undefined' ? window.location.origin : ''}/share/${settingsDemo?.id}`}
                  />
                  <Button
                    variant="outline"
                    onClick={() => {
                      navigator.clipboard.writeText(`${window.location.origin}/share/${settingsDemo?.id}`)
                    }}
                  >
                    Copy
                  </Button>
                </div>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setSettingsDemo(null)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={!!shareDemo} onOpenChange={() => setShareDemo(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Share Demo</DialogTitle>
            <DialogDescription>
              Share this demo with others
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            {!shareDemo?.is_public && (
              <div className="p-4 rounded-lg bg-yellow-50 border border-yellow-200 text-yellow-800 text-sm">
                This demo is private. Make it public to share with others.
              </div>
            )}
            <div className="space-y-2">
              <Label>Share Link</Label>
              <div className="flex gap-2">
                <Input
                  readOnly
                  value={`${typeof window !== 'undefined' ? window.location.origin : ''}/share/${shareDemo?.id}`}
                />
                <Button onClick={handleCopyShareLink}>
                  {copied ? "Copied!" : "Copy"}
                </Button>
              </div>
            </div>
            {!shareDemo?.is_public && (
              <Button
                className="w-full"
                onClick={() => {
                  handleTogglePublic(shareDemo?.id, true)
                  setShareDemo({ ...shareDemo, is_public: true })
                }}
              >
                <Globe className="h-4 w-4 mr-2" />
                Make Public
              </Button>
            )}
          </div>
        </DialogContent>
      </Dialog>

      <AlertDialog open={!!deleteDemo} onOpenChange={() => setDeleteDemo(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Demo</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete "{deleteDemo?.title}"? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteDemo}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
