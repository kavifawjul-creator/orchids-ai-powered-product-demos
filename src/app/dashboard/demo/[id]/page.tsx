"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { useParams } from "next/navigation"
import { motion, Reorder, AnimatePresence } from "framer-motion"
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
  Check,
  Sparkles,
  Loader2,
  MousePointer2
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
import { supabase } from "@/lib/supabase"

export default function DemoDetailPage() {
  const { id } = useParams()
  const [demo, setDemo] = useState<any>(null)
  const [clips, setClips] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [isPlaying, setIsPlaying] = useState(false)
  const [activeClipId, setActiveClipId] = useState<string | null>(null)
  const [isCopied, setIsCopied] = useState(false)
  const [playbackProgress, setPlaybackProgress] = useState(0)
  const [isMagicGenerating, setIsMagicGenerating] = useState(false)
  const [brandColor, setBrandColor] = useState("#7c3aed")

  useEffect(() => {
    async function fetchData() {
      const { data: demoData } = await supabase
        .from('demos')
        .select('*')
        .eq('id', id)
        .single()
      
      if (demoData) {
        setDemo(demoData)
        setBrandColor(demoData.brand_color || "#7c3aed")
      }

      const { data: clipsData } = await supabase
        .from('clips')
        .select('*')
        .eq('demo_id', id)
        .order('order_index', { ascending: true })
      
      if (clipsData) {
        setClips(clipsData)
        if (clipsData.length > 0) {
          setActiveClipId(clipsData[0].id)
        }
      }
      setLoading(false)
    }
    fetchData()
  }, [id])

  const activeClip = clips.find(c => c.id === activeClipId) || clips[0]

  const saveClip = async (clipId: string, updates: any) => {
    await supabase
      .from('clips')
      .update(updates)
      .eq('id', clipId)
  }

  const saveDemo = async (updates: any) => {
    await supabase
      .from('demos')
      .update(updates)
      .eq('id', id)
  }

  const handleReorder = async (newClips: any[]) => {
    setClips(newClips)
    // Batch update order_index
    const updates = newClips.map((c, i) => ({
      id: c.id,
      order_index: i
    }))

    for (const update of updates) {
      await supabase
        .from('clips')
        .update({ order_index: update.order_index })
        .eq('id', update.id)
    }
  }

  const copyLink = () => {
    const baseUrl = process.env.NEXT_PUBLIC_APP_URL || (typeof window !== 'undefined' ? window.location.origin : 'http://localhost:3000')
    const url = `${baseUrl}/share/${id}`
    navigator.clipboard.writeText(url)
    setIsCopied(true)
    setTimeout(() => setIsCopied(false), 2000)
  }

  const handleMagicNarration = () => {
    setIsMagicGenerating(true)
    setTimeout(async () => {
      const suggestions = [
        "In this section, we highlight the intuitive interface designed for maximum productivity.",
        "Notice how the data seamlessly flows between components, providing a unified experience.",
        "Our proprietary AI engine works in the background to optimize every single interaction you see here.",
        "The responsiveness of the platform ensures that users stay engaged and focused on their tasks."
      ]
      const randomSuggestion = suggestions[Math.floor(Math.random() * suggestions.length)]
      const newClips = clips.map(c => c.id === activeClipId ? {...c, narration: randomSuggestion} : c)
      setClips(newClips)
      if (activeClipId) {
        await saveClip(activeClipId, { narration: randomSuggestion })
      }
      setIsMagicGenerating(false)
    }, 1500)
  }

  if (loading) {
    return <div className="flex items-center justify-center h-full">
      <Loader2 className="h-8 w-8 animate-spin text-primary" />
    </div>
  }

  if (!demo) {
    return <div className="text-center p-12">Demo not found</div>
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
              <h2 className="text-2xl font-bold tracking-tight">{demo.title}</h2>
              <Badge variant="outline">{demo.status}</Badge>
            </div>
            <p className="text-sm text-muted-foreground flex items-center gap-2">
              <Clock className="h-3 w-3" /> Updated {new Date(demo.updated_at).toLocaleDateString()} • {demo.repo_url}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button 
            variant="outline" 
            className="gap-2"
            onClick={() => {
              setIsPlaying(true)
              setPlaybackProgress(0)
            }}
          >
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
                        defaultValue={typeof window !== 'undefined' ? `${window.location.origin}/share/${id}` : `${process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000'}/share/${id}`}
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
            {/* Video Player */}
            <Card className="flex-1 bg-black overflow-hidden relative group border-none shadow-2xl rounded-2xl aspect-video max-h-[500px]">
              <AnimatePresence mode="wait">
                <motion.div
                  key={activeClipId + (isPlaying ? "_playing" : "_static")}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="absolute inset-0"
                >
                  {isPlaying && activeClip?.video_url ? (
                    <video
                      src={activeClip.video_url}
                      className="w-full h-full object-cover"
                      autoPlay
                      onEnded={() => setIsPlaying(false)}
                      onTimeUpdate={(e) => {
                        const video = e.currentTarget;
                        setPlaybackProgress((video.currentTime / video.duration) * 100);
                      }}
                    />
                  ) : activeClip?.thumbnail_url ? (
                    <img 
                      src={activeClip.thumbnail_url} 
                      alt={activeClip.title} 
                      className="w-full h-full object-cover opacity-60"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center bg-muted">
                      <Video className="h-12 w-12 text-muted-foreground/20" />
                    </div>
                  )}
                </motion.div>
              </AnimatePresence>


              {/* Title Card Overlay */}
              <AnimatePresence>
                {activeClip?.overlay?.show && (
                  <motion.div 
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 1.1 }}
                    className="absolute inset-0 flex items-center justify-center z-20 bg-black/40 backdrop-blur-[2px]"
                  >
                    <div className="text-center space-y-4">
                      <motion.div 
                        initial={{ width: 0 }}
                        animate={{ width: "100%" }}
                        className="h-1 bg-primary mx-auto"
                      />
                      <h2 className="text-4xl md:text-6xl font-black tracking-tighter text-white uppercase italic">
                        {activeClip.overlay.text}
                      </h2>
                      <motion.div 
                        initial={{ width: 0 }}
                        animate={{ width: "100%" }}
                        transition={{ delay: 0.2 }}
                        className="h-1 bg-primary mx-auto"
                      />
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Captions Overlay */}
              {activeClip?.captions && isPlaying && (
                <div className="absolute bottom-24 left-0 right-0 flex justify-center z-30 px-12">
                  <motion.div 
                    initial={{ y: 20, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    className="bg-black/80 backdrop-blur-md px-4 py-2 rounded-lg border border-white/10 text-white text-sm font-medium text-center shadow-2xl"
                  >
                    {activeClip.captions}
                  </motion.div>
                </div>
              )}

              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center space-y-4 z-10">
                  {!isPlaying && <Play className="h-16 w-16 text-white/80 mx-auto drop-shadow-lg cursor-pointer hover:scale-110 transition-transform" onClick={() => setIsPlaying(true)} />}
                  <div className="space-y-1">
                     <p className="text-white font-bold text-xl drop-shadow-md">{activeClip?.title}</p>
                     <p className="text-white/60 font-mono text-xs">autonomous_recording_clip_{activeClipId?.slice(0, 4)}.mp4</p>
                  </div>
                </div>
              </div>

            {/* AI Agent Cursor Simulation (only when playing) */}
            {isPlaying && (
              <motion.div 
                className="absolute z-20 pointer-events-none"
                animate={{ 
                  x: [100, 300, 200, 400, 100],
                  y: [100, 200, 400, 150, 100],
                }}
                transition={{ repeat: Infinity, duration: 5 }}
              >
                <MousePointer2 className="h-8 w-8 text-primary fill-primary drop-shadow-xl" />
              </motion.div>
            )}
            
            {/* Player Controls */}
            <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/90 via-black/40 to-transparent p-6 opacity-0 group-hover:opacity-100 transition-opacity">
              <div className="space-y-4">
                <div className="h-1.5 w-full bg-white/20 rounded-full overflow-hidden cursor-pointer">
                  <motion.div 
                    className="h-full" 
                    style={{ backgroundColor: brandColor }}
                    animate={{ width: isPlaying ? "100%" : `${playbackProgress}%` }}
                    transition={isPlaying ? { duration: 10, ease: "linear" } : { duration: 0.3 }}
                  />
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
                    <span className="text-sm font-mono">{isPlaying ? "0:04" : activeClip?.duration} / 2:22</span>
                  </div>
                  <div className="flex items-center gap-4 text-xs font-mono text-white/60">
                    <span className="flex items-center gap-1">
                      <div className="h-1.5 w-1.5 rounded-full bg-red-500 animate-pulse" />
                      AUTONOMOUS RENDERING
                    </span>
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
                onReorder={handleReorder}
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
                    <img src={clip.thumbnail_url} alt={clip.title} className="absolute inset-0 w-full h-full object-cover transition-transform group-hover:scale-110" />
                    <div className="absolute inset-0 bg-black/40 p-3 flex flex-col justify-between group">
                      <div className="flex justify-between items-start">
                        <GripVertical className="h-4 w-4 text-white/50 cursor-grab opacity-0 group-hover:opacity-100 transition-opacity" />
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
                  <label className="text-sm font-medium leading-none">
                    Clip Title
                  </label>
                  <Input 
                    value={activeClip?.title || ""}
                    onChange={(e) => {
                      const newClips = clips.map(c => c.id === activeClipId ? {...c, title: e.target.value} : c);
                      setClips(newClips);
                      if (activeClipId) saveClip(activeClipId, { title: e.target.value });
                    }}
                  />
                </div>
                
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <label className="text-sm font-medium leading-none">
                      AI Narration
                    </label>
                    <Badge variant="secondary" className="text-[10px] uppercase font-mono py-0 h-4">Voice: Alloy</Badge>
                  </div>
                  <Textarea 
                    className="h-32 resize-none"
                    placeholder="Enter what the AI should say during this clip..."
                    value={activeClip?.narration || ""}
                    onChange={(e) => {
                      const newClips = clips.map(c => c.id === activeClipId ? {...c, narration: e.target.value} : c);
                      setClips(newClips);
                      if (activeClipId) saveClip(activeClipId, { narration: e.target.value });
                    }}
                  />
                  <div className="flex gap-2">
                    <Button 
                      variant="outline" 
                      size="sm" 
                      className="w-full gap-2 relative overflow-hidden"
                      onClick={handleMagicNarration}
                      disabled={isMagicGenerating}
                    >
                      {isMagicGenerating ? (
                        <>
                          <Loader2 className="h-3.5 w-3.5 animate-spin" />
                          Analyzing clip...
                        </>
                      ) : (
                        <>
                          <Sparkles className="h-3.5 w-3.5 text-primary" /> 
                          Magic AI Suggestion
                        </>
                      )}
                    </Button>
                    <Button variant="ghost" size="sm" className="w-10 px-0">
                      <Mic className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                </div>

                <Separator />

                  <div className="space-y-4">
                    <h4 className="text-sm font-semibold">Overlays</h4>
                    <div className="grid grid-cols-2 gap-2">
                      <Button 
                        variant={activeClip?.overlay?.show ? "default" : "outline"} 
                        className="justify-start gap-2 h-10 px-3 transition-all"
                        onClick={() => {
                          const newOverlay = {...activeClip?.overlay, show: !activeClip?.overlay?.show, text: activeClip?.overlay?.text || activeClip?.title};
                          const newClips = clips.map(c => c.id === activeClipId ? {...c, overlay: newOverlay} : c);
                          setClips(newClips);
                          if (activeClipId) saveClip(activeClipId, { overlay: newOverlay });
                        }}
                      >
                        <Type className="h-4 w-4" /> Title Card
                      </Button>
                      <Button 
                        variant={activeClip?.captions ? "default" : "outline"} 
                        className="justify-start gap-2 h-10 px-3 transition-all"
                        onClick={() => {
                          const newCaptions = activeClip.captions ? "" : "Entering magic link credentials...";
                          const newClips = clips.map(c => c.id === activeClipId ? {...c, captions: newCaptions} : c);
                          setClips(newClips);
                          if (activeClipId) saveClip(activeClipId, { captions: newCaptions });
                        }}
                      >
                        <MessageSquare className="h-4 w-4" /> Captions
                      </Button>
                      <Button variant="outline" className="justify-start gap-2 h-10 px-3 hover:bg-primary/5 hover:border-primary/50 transition-all">
                        <MousePointer2 className="h-4 w-4" /> Click Effects
                      </Button>
                      <Button variant="outline" className="justify-start gap-2 h-10 px-3 hover:bg-primary/5 hover:border-primary/50 transition-all">
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
                        onClick={() => {
                          setBrandColor(color)
                          saveDemo({ brand_color: color })
                        }}
                        className={`h-10 rounded-lg border-2 transition-all shadow-sm ${brandColor === color ? 'border-primary scale-110' : 'border-transparent hover:border-primary/50'}`} 
                        style={{ backgroundColor: color }}
                      />
                    ))}
                  </div>
                </div>
                
                <div className="space-y-2">
                  <h4 className="text-sm font-semibold">AI Voice Actor</h4>
                  <div className="space-y-2">
                    {[
                      { name: "Echo", desc: "Masculine, Deep", active: false },
                      { name: "Nova", desc: "Feminine, Energetic", active: true },
                      { name: "Alloy", desc: "Neutral, Professional", active: false }
                    ].map((voice) => (
                      <div key={voice.name} className={`flex items-center justify-between p-3 rounded-xl border hover:border-primary/50 cursor-pointer transition-all ${voice.active ? 'bg-primary/5 border-primary' : 'bg-muted/30'}`}>
                        <div>
                          <p className="text-sm font-bold">{voice.name}</p>
                          <p className="text-[10px] text-muted-foreground">{voice.desc}</p>
                        </div>
                        <div className="h-8 w-8 rounded-full bg-background flex items-center justify-center border shadow-sm hover:scale-110 transition-transform">
                          <Play className="h-3 w-3 fill-current" />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="space-y-2">
                  <h4 className="text-sm font-semibold">Background Music</h4>
                  <div className="p-4 rounded-xl border border-dashed bg-muted/50 flex flex-col items-center gap-2">
                    <p className="text-xs text-muted-foreground italic">"Corporate Minimal Tech" selected</p>
                    <Button variant="outline" size="sm" className="h-8 text-[10px]">Change Track</Button>
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
