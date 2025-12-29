
"use client"

import { useState } from "react"
import Link from "next/link"
import { useParams } from "next/navigation"
import { motion, Reorder } from "framer-motion"
import { 
  Play, 
  Pause, 
  SkipBack, 
  SkipForward, 
  Share2, 
  Settings, 
  Download, 
  Plus, 
  GripVertical, 
  MessageSquare, 
  Clock, 
  ChevronLeft,
  Eye,
  Type,
  Mic,
  MoreHorizontal,
  Copy,
  Globe,
  Lock,
  Check
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter
} from "@/components/ui/dialog"
import { Switch } from "@/components/ui/switch"

const initialClips = [
  {
    id: "clip-1",
    title: "Introduction & Login",
    duration: "0:12",
    thumbnail: "https://images.unsplash.com/photo-1614332287897-cdc485fa562d?w=200&h=112&fit=crop",
    narration: "We'll start by showing the simple login process with magic links.",
  },
  {
    id: "clip-2",
    title: "Analytics Dashboard Overview",
    duration: "0:45",
    thumbnail: "https://images.unsplash.com/photo-1551288049-bbda3865c170?w=200&h=112&fit=crop",
    narration: "The dashboard provides a real-time view of all your key performance indicators.",
  },
  {
    id: "clip-3",
    title: "Custom Report Generation",
    duration: "1:15",
    thumbnail: "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=200&h=112&fit=crop",
    narration: "Users can generate complex reports in seconds using our AI-assisted query builder.",
  },
  {
    id: "clip-4",
    title: "Closing & Call to Action",
    duration: "0:10",
    thumbnail: "https://images.unsplash.com/photo-1531297484001-80022131f5a1?w=200&h=112&fit=crop",
    narration: "Get started today for free and transform your data into insights.",
  },
]

export default function DemoDetailPage() {
  const { id } = useParams()
  const [clips, setClips] = useState(initialClips)
  const [isPlaying, setIsPlaying] = useState(false)
  const [activeClipId, setActiveClipId] = useState("clip-1")
  const [isCopied, setIsCopied] = useState(false)

  const copyLink = () => {
    navigator.clipboard.writeText(`https://autovid.ai/share/${id}`)
    setIsCopied(true)
    setTimeout(() => setIsCopied(false), 2000)
  }

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <Link href="/dashboard">
            <Button variant="ghost" size="icon" className="rounded-full">
              <ChevronLeft className="h-5 w-5" />
            </Button>
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-2xl font-bold tracking-tight">Onboarding Flow Walkthrough</h2>
              <Badge variant="outline">Draft</Badge>
            </div>
            <p className="text-sm text-muted-foreground flex items-center gap-2">
              <Clock className="h-3 w-3" /> Updated 2 hours ago • github.com/acme/app
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" className="gap-2">
            <Eye className="h-4 w-4" /> Preview
          </Button>
          
          <Dialog>
            <DialogTrigger asChild>
              <Button variant="outline" className="gap-2">
                <Share2 className="h-4 w-4" /> Share
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-md">
              <DialogHeader>
                <DialogTitle>Share Autonomous Demo</DialogTitle>
                <DialogDescription>
                  Anyone with the link will be able to view this autonomous walkthrough.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-6 py-4">
                <div className="flex items-center justify-between space-x-2">
                  <div className="flex items-center gap-2">
                    <Globe className="h-4 w-4 text-muted-foreground" />
                    <div className="space-y-0.5">
                      <p className="text-sm font-medium">Public link</p>
                      <p className="text-xs text-muted-foreground">Make this demo visible to the web.</p>
                    </div>
                  </div>
                  <Switch defaultChecked />
                </div>
                <div className="flex items-center space-x-2">
                  <div className="grid flex-1 gap-2">
                    <Input
                      id="link"
                      defaultValue={`https://autovid.ai/share/${id}`}
                      readOnly
                      className="font-mono text-xs"
                    />
                  </div>
                  <Button size="sm" className="px-3" onClick={copyLink}>
                    <span className="sr-only">Copy</span>
                    {isCopied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                  </Button>
                </div>
                <Separator />
                <div className="space-y-2">
                  <p className="text-sm font-medium">Permissions</p>
                  <div className="flex items-center gap-2 p-2 rounded-lg border bg-muted/30">
                    <Lock className="h-4 w-4 text-muted-foreground" />
                    <span className="text-xs">Password protection (Pro feature)</span>
                  </div>
                </div>
              </div>
              <DialogFooter className="sm:justify-start">
                <Button type="button" variant="secondary">
                  Close
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>

          <Button className="gap-2">
            <Download className="h-4 w-4" /> Export
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 flex-1 overflow-hidden">
        {/* Main Editor Area */}
        <div className="lg:col-span-8 flex flex-col gap-6 overflow-hidden">
          {/* Video Player Placeholder */}
          <Card className="flex-1 bg-black overflow-hidden relative group border-none shadow-2xl rounded-2xl aspect-video max-h-[500px]">
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center space-y-4">
                <Play className="h-16 w-16 text-white/50 mx-auto" />
                <p className="text-white/30 font-mono text-sm">autonomous_demo_v1.mp4</p>
              </div>
            </div>
            
            {/* Player Controls */}
            <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-6 opacity-0 group-hover:opacity-100 transition-opacity">
              <div className="space-y-4">
                <div className="h-1.5 w-full bg-white/20 rounded-full overflow-hidden">
                  <div className="h-full bg-primary w-1/3" />
                </div>
                <div className="flex items-center justify-between text-white">
                  <div className="flex items-center gap-6">
                    <button className="hover:text-primary transition-colors">
                      <SkipBack className="h-5 w-5 fill-current" />
                    </button>
                    <button 
                      onClick={() => setIsPlaying(!isPlaying)}
                      className="bg-white text-black p-2 rounded-full hover:scale-105 transition-transform"
                    >
                      {isPlaying ? <Pause className="h-6 w-6 fill-current" /> : <Play className="h-6 w-6 fill-current" />}
                    </button>
                    <button className="hover:text-primary transition-colors">
                      <SkipForward className="h-5 w-5 fill-current" />
                    </button>
                    <span className="text-sm font-mono">0:24 / 2:22</span>
                  </div>
                  <div className="flex items-center gap-4">
                    <button className="hover:text-primary transition-colors">
                      <Settings className="h-5 w-5" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </Card>

          {/* Timeline / Storyboard */}
          <div className="flex-1 overflow-hidden flex flex-col">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
                <MessageSquare className="h-4 w-4" /> Storyboard
              </h3>
              <Button variant="ghost" size="sm" className="h-8 gap-1">
                <Plus className="h-4 w-4" /> Add Clip
              </Button>
            </div>
            <div className="overflow-x-auto pb-4 custom-scrollbar">
              <Reorder.Group 
                axis="x" 
                values={clips} 
                onReorder={setClips}
                className="flex gap-4 min-w-max"
              >
                {clips.map((clip) => (
                  <Reorder.Item 
                    key={clip.id} 
                    value={clip}
                    onClick={() => setActiveClipId(clip.id)}
                    className={`
                      relative w-56 h-32 rounded-xl border-2 transition-all cursor-pointer overflow-hidden
                      ${activeClipId === clip.id ? "border-primary ring-2 ring-primary/20" : "border-border hover:border-primary/50"}
                    `}
                  >
                    <img src={clip.thumbnail} alt={clip.title} className="absolute inset-0 w-full h-full object-cover" />
                    <div className="absolute inset-0 bg-black/40 p-3 flex flex-col justify-between">
                      <div className="flex justify-between items-start">
                        <GripVertical className="h-4 w-4 text-white/50 cursor-grab" />
                        <Badge variant="secondary" className="bg-black/60 text-white border-none text-[10px] h-5 px-1.5">
                          {clip.duration}
                        </Badge>
                      </div>
                      <p className="text-xs text-white font-medium line-clamp-1">{clip.title}</p>
                    </div>
                  </Reorder.Item>
                ))}
              </Reorder.Group>
            </div>
          </div>
        </div>

        {/* Sidebar Controls */}
        <div className="lg:col-span-4 flex flex-col gap-6 overflow-hidden">
          <Tabs defaultValue="clip" className="h-full flex flex-col">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="clip">Clip Settings</TabsTrigger>
              <TabsTrigger value="global">Global Styles</TabsTrigger>
            </TabsList>
            
            <TabsContent value="clip" className="flex-1 overflow-y-auto pt-4 space-y-6 px-1">
              <div className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                    Clip Title
                  </label>
                  <Input 
                    value={clips.find(c => c.id === activeClipId)?.title}
                    onChange={(e) => {
                      const newClips = clips.map(c => c.id === activeClipId ? {...c, title: e.target.value} : c);
                      setClips(newClips);
                    }}
                  />
                </div>
                
                <div className="space-y-2">
                  <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                    AI Narration
                  </label>
                  <Textarea 
                    className="h-32 resize-none"
                    placeholder="Enter what the AI should say during this clip..."
                    value={clips.find(c => c.id === activeClipId)?.narration}
                    onChange={(e) => {
                      const newClips = clips.map(c => c.id === activeClipId ? {...c, narration: e.target.value} : c);
                      setClips(newClips);
                    }}
                  />
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" className="w-full gap-2">
                      <Mic className="h-3.5 w-3.5" /> Regenerate Voice
                    </Button>
                  </div>
                </div>

                <Separator />

                <div className="space-y-4">
                  <h4 className="text-sm font-semibold">Overlays</h4>
                  <div className="grid grid-cols-2 gap-2">
                    <Button variant="outline" className="justify-start gap-2 h-10 px-3">
                      <Type className="h-4 w-4" /> Title Card
                    </Button>
                    <Button variant="outline" className="justify-start gap-2 h-10 px-3">
                      <MessageSquare className="h-4 w-4" /> Captions
                    </Button>
                    <Button variant="outline" className="justify-start gap-2 h-10 px-3">
                      <MousePointer2 className="h-4 w-4" /> Click Effects
                    </Button>
                    <Button variant="outline" className="justify-start gap-2 h-10 px-3">
                      <Sparkles className="h-4 w-4" /> AI Zoom
                    </Button>
                  </div>
                </div>
              </div>
            </TabsContent>
            
            <TabsContent value="global" className="flex-1 overflow-y-auto pt-4 space-y-6 px-1">
              <div className="space-y-4">
                <div className="space-y-2">
                  <h4 className="text-sm font-semibold">Brand Identity</h4>
                  <div className="grid grid-cols-4 gap-2">
                    {["#000000", "#7c3aed", "#3b82f6", "#10b981"].map((color) => (
                      <button 
                        key={color} 
                        className="h-8 rounded-md border" 
                        style={{ backgroundColor: color }}
                      />
                    ))}
                  </div>
                </div>
                
                <div className="space-y-2">
                  <h4 className="text-sm font-semibold">AI Voice Actor</h4>
                  <div className="space-y-2">
                    {["Echo (Masculine, Deep)", "Nova (Feminine, Energetic)", "Alloy (Neutral, Professional)"].map((voice) => (
                      <div key={voice} className="flex items-center justify-between p-2 rounded-lg border hover:bg-muted cursor-pointer transition-colors">
                        <span className="text-sm">{voice}</span>
                        <Play className="h-3 w-3" />
                      </div>
                    ))}
                  </div>
                </div>

                <div className="space-y-2">
                  <h4 className="text-sm font-semibold">Background Music</h4>
                  <div className="p-4 rounded-lg border bg-muted/50 text-center">
                    <p className="text-xs text-muted-foreground italic">"Corporate Minimal Tech" selected</p>
                  </div>
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  )
}

function MousePointer2(props: any) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M4.01 4.01 10 20l4-6 6-4Z" />
      <path d="m13 13 3 3" />
    </svg>
  )
}

function Sparkles(props: any) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z" />
      <path d="M5 3v4" />
      <path d="M19 17v4" />
      <path d="M3 5h4" />
      <path d="M17 19h4" />
    </svg>
  )
}
