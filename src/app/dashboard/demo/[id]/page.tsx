"use client"

import React, { useState, useEffect } from "react"
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
  MousePointer2,
  Video,
  Volume2,
  VolumeX,
  RefreshCw,
  Scissors
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
import { createClient } from "@/lib/supabase/client"
import { ClipTrimmer, TextOverlayEditor } from "@/components/editor/ClipTrimmer"

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
  const [selectedVoice, setSelectedVoice] = useState("nova")
  const [availableVoices, setAvailableVoices] = useState<{ id: string, name: string, description: string }[]>([])
  const [isGeneratingAudio, setIsGeneratingAudio] = useState(false)
  const [audioPreview, setAudioPreview] = useState<string | null>(null)
  const [isPlayingPreview, setIsPlayingPreview] = useState(false)
  const [showTrimmer, setShowTrimmer] = useState(false)
  const [isSavingTrim, setIsSavingTrim] = useState(false)
  // Visual effects state
  const [showIntroDialog, setShowIntroDialog] = useState(false)
  const [showOutroDialog, setShowOutroDialog] = useState(false)
  const [introTitle, setIntroTitle] = useState("")
  const [introSubtitle, setIntroSubtitle] = useState("")
  const [outroText, setOutroText] = useState("Try it now!")
  const [outroUrl, setOutroUrl] = useState("")
  const [isGeneratingIntro, setIsGeneratingIntro] = useState(false)
  const [selectedClickEffect, setSelectedClickEffect] = useState("none")
  const [selectedZoomEffect, setSelectedZoomEffect] = useState("none")
  const audioRef = React.useRef<HTMLAudioElement | null>(null)
  const supabase = createClient()
  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

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

  // Fetch available voices on mount
  useEffect(() => {
    async function fetchVoices() {
      try {
        const res = await fetch(`${API_URL}/api/v1/editor/voices`)
        if (res.ok) {
          const data = await res.json()
          setAvailableVoices(data.voices || [])
        }
      } catch (e) {
        // Fallback voices if API unavailable
        setAvailableVoices([
          { id: "alloy", name: "Alloy", description: "Neutral and balanced" },
          { id: "echo", name: "Echo", description: "Warm and natural" },
          { id: "fable", name: "Fable", description: "British accent" },
          { id: "onyx", name: "Onyx", description: "Deep and authoritative" },
          { id: "nova", name: "Nova", description: "Friendly and conversational" },
          { id: "shimmer", name: "Shimmer", description: "Clear and expressive" },
        ])
      }
    }
    fetchVoices()
  }, [])

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
      const newClips = clips.map(c => c.id === activeClipId ? { ...c, narration: randomSuggestion } : c)
      setClips(newClips)
      if (activeClipId) {
        await saveClip(activeClipId, { narration: randomSuggestion })
      }
      setIsMagicGenerating(false)
    }, 1500)
  }

  // Generate TTS audio for narration
  const handleGenerateNarration = async () => {
    if (!activeClip?.narration || !activeClipId) return

    setIsGeneratingAudio(true)
    try {
      const res = await fetch(`${API_URL}/api/v1/demos/${id}/clips/${activeClipId}/narration`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: activeClip.narration,
          voice: selectedVoice,
          speed: 1.0
        })
      })

      if (res.ok) {
        const data = await res.json()
        // Update clip with audio URL
        const newClips = clips.map(c =>
          c.id === activeClipId ? { ...c, audio_url: data.audio_url, voice_id: selectedVoice } : c
        )
        setClips(newClips)
      }
    } catch (e) {
      console.error('Failed to generate narration:', e)
    } finally {
      setIsGeneratingAudio(false)
    }
  }

  // Preview narration audio
  const handlePreviewNarration = async () => {
    if (!activeClip?.narration) return

    setIsGeneratingAudio(true)
    try {
      const res = await fetch(`${API_URL}/api/v1/demos/${id}/narration/preview`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: activeClip.narration.slice(0, 200), // Preview first 200 chars
          voice: selectedVoice,
          speed: 1.0
        })
      })

      if (res.ok) {
        const data = await res.json()
        setAudioPreview(`data:audio/mp3;base64,${data.audio_data}`)
        // Auto-play preview
        if (audioRef.current) {
          audioRef.current.src = `data:audio/mp3;base64,${data.audio_data}`
          audioRef.current.play()
          setIsPlayingPreview(true)
        }
      }
    } catch (e) {
      console.error('Failed to preview narration:', e)
    } finally {
      setIsGeneratingAudio(false)
    }
  }

  // Stop audio preview
  const stopAudioPreview = () => {
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current.currentTime = 0
    }
    setIsPlayingPreview(false)
  }

  // Parse duration string like "00:30" to seconds
  const parseDuration = (duration: string | number): number => {
    if (typeof duration === 'number') return duration
    const parts = duration.split(':')
    if (parts.length === 2) {
      return parseInt(parts[0]) * 60 + parseInt(parts[1])
    }
    return 30 // Default fallback
  }

  // Handle trim change (local state update)
  const handleTrimChange = (start: number, end: number | null) => {
    if (!activeClipId) return
    const newClips = clips.map(c =>
      c.id === activeClipId ? { ...c, trim_start: start, trim_end: end } : c
    )
    setClips(newClips)
  }

  // Save trim to backend
  const handleSaveTrim = async () => {
    if (!activeClip || !activeClipId) return

    setIsSavingTrim(true)
    try {
      const res = await fetch(
        `${API_URL}/api/v1/demos/${id}/clips/${activeClipId}/trim?trim_start=${activeClip.trim_start || 0}&trim_end=${activeClip.trim_end || ''}`,
        { method: 'POST' }
      )

      if (res.ok) {
        await saveClip(activeClipId, {
          trim_start: activeClip.trim_start,
          trim_end: activeClip.trim_end
        })
      }
    } catch (e) {
      console.error('Failed to save trim:', e)
    } finally {
      setIsSavingTrim(false)
    }
  }

  // Split clip at a point
  const handleSplitClip = async (splitPoint: number) => {
    if (!activeClipId) return

    try {
      const res = await fetch(
        `${API_URL}/api/v1/demos/${id}/clips/${activeClipId}/split?split_point=${splitPoint}`,
        { method: 'POST' }
      )

      if (res.ok) {
        const data = await res.json()
        // Refresh clips from database
        const { data: clipsData } = await supabase
          .from('clips')
          .select('*')
          .eq('demo_id', id)
          .order('order_index', { ascending: true })

        if (clipsData) {
          setClips(clipsData)
        }
      }
    } catch (e) {
      console.error('Failed to split clip:', e)
    }
  }

  // Handle text overlay add
  const handleAddOverlay = async (overlay: { text: string; position_x: number; position_y: number; font_size: number; font_color: string; background_color: string; animation: string }) => {
    if (!activeClipId) return

    try {
      const res = await fetch(`${API_URL}/api/v1/demos/${id}/clips/${activeClipId}/overlays`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(overlay)
      })

      if (res.ok) {
        const data = await res.json()
        // Update local state
        const existingOverlay = activeClip?.overlay || { text_overlays: [] }
        const newOverlays = [...(existingOverlay.text_overlays || []), { id: data.overlay_id, ...overlay }]
        const newClips = clips.map(c =>
          c.id === activeClipId ? { ...c, overlay: { ...existingOverlay, text_overlays: newOverlays } } : c
        )
        setClips(newClips)
      }
    } catch (e) {
      console.error('Failed to add overlay:', e)
    }
  }

  // Handle text overlay remove
  const handleRemoveOverlay = async (overlayId: string) => {
    if (!activeClipId) return

    try {
      await fetch(`${API_URL}/api/v1/demos/${id}/clips/${activeClipId}/overlays/${overlayId}`, {
        method: 'DELETE'
      })

      // Update local state
      const existingOverlay = activeClip?.overlay || { text_overlays: [] }
      const newOverlays = (existingOverlay.text_overlays || []).filter((o: any) => o.id !== overlayId)
      const newClips = clips.map(c =>
        c.id === activeClipId ? { ...c, overlay: { ...existingOverlay, text_overlays: newOverlays } } : c
      )
      setClips(newClips)
    } catch (e) {
      console.error('Failed to remove overlay:', e)
    }
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

          <Button className="gap-2" onClick={() => {
            if (demo?.video_url) {
              window.open(demo.video_url, '_blank')
            }
          }}>
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
                      const newClips = clips.map(c => c.id === activeClipId ? { ...c, title: e.target.value } : c);
                      setClips(newClips);
                      if (activeClipId) saveClip(activeClipId, { title: e.target.value });
                    }}
                  />
                </div>

                {/* Clip Trimming Section */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <label className="text-sm font-medium leading-none flex items-center gap-2">
                      <Scissors className="h-3.5 w-3.5" />
                      Trim & Split
                    </label>
                    <Button
                      variant={showTrimmer ? "default" : "outline"}
                      size="sm"
                      className="h-6 text-[10px] px-2"
                      onClick={() => setShowTrimmer(!showTrimmer)}
                    >
                      {showTrimmer ? "Hide" : "Show"} Editor
                    </Button>
                  </div>

                  {showTrimmer && activeClip && (
                    <ClipTrimmer
                      clipId={activeClip.id}
                      duration={parseDuration(activeClip.duration)}
                      trimStart={activeClip.trim_start || 0}
                      trimEnd={activeClip.trim_end || null}
                      videoUrl={activeClip.video_url}
                      onTrimChange={handleTrimChange}
                      onSplit={handleSplitClip}
                      onSave={handleSaveTrim}
                      isSaving={isSavingTrim}
                    />
                  )}

                  {!showTrimmer && activeClip && (activeClip.trim_start > 0 || activeClip.trim_end) && (
                    <div className="text-[10px] text-muted-foreground bg-muted/50 px-2 py-1 rounded flex items-center gap-1">
                      <Check className="h-3 w-3 text-green-500" />
                      Trimmed: {activeClip.trim_start}s - {activeClip.trim_end || 'end'}
                    </div>
                  )}
                </div>

                <Separator />

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <label className="text-sm font-medium leading-none">
                      AI Narration
                    </label>
                    <select
                      value={selectedVoice}
                      onChange={(e) => setSelectedVoice(e.target.value)}
                      className="text-[10px] uppercase font-mono py-1 px-2 rounded border bg-background"
                    >
                      {availableVoices.map(v => (
                        <option key={v.id} value={v.id}>{v.name}</option>
                      ))}
                    </select>
                  </div>
                  <Textarea
                    className="h-32 resize-none"
                    placeholder="Enter what the AI should say during this clip..."
                    value={activeClip?.narration || ""}
                    onChange={(e) => {
                      const newClips = clips.map(c => c.id === activeClipId ? { ...c, narration: e.target.value } : c);
                      setClips(newClips);
                      if (activeClipId) saveClip(activeClipId, { narration: e.target.value });
                    }}
                  />
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      className="flex-1 gap-2"
                      onClick={handleMagicNarration}
                      disabled={isMagicGenerating}
                    >
                      {isMagicGenerating ? (
                        <>
                          <Loader2 className="h-3.5 w-3.5 animate-spin" />
                          Analyzing...
                        </>
                      ) : (
                        <>
                          <Sparkles className="h-3.5 w-3.5 text-primary" />
                          AI Suggest
                        </>
                      )}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="gap-1"
                      onClick={handlePreviewNarration}
                      disabled={isGeneratingAudio || !activeClip?.narration}
                      title="Preview voice"
                    >
                      {isGeneratingAudio ? (
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      ) : isPlayingPreview ? (
                        <VolumeX className="h-3.5 w-3.5" onClick={(e) => { e.stopPropagation(); stopAudioPreview(); }} />
                      ) : (
                        <Volume2 className="h-3.5 w-3.5" />
                      )}
                    </Button>
                    <Button
                      variant="default"
                      size="sm"
                      className="gap-1"
                      onClick={handleGenerateNarration}
                      disabled={isGeneratingAudio || !activeClip?.narration}
                      title="Generate audio"
                    >
                      {isGeneratingAudio ? (
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      ) : (
                        <Mic className="h-3.5 w-3.5" />
                      )}
                    </Button>
                  </div>
                  {activeClip?.audio_url && (
                    <div className="flex items-center gap-2 text-[10px] text-green-600 bg-green-50 px-2 py-1 rounded">
                      <Check className="h-3 w-3" />
                      Audio generated with {activeClip.voice_id || 'default'} voice
                    </div>
                  )}
                  {/* Hidden audio element for preview playback */}
                  <audio
                    ref={audioRef}
                    onEnded={() => setIsPlayingPreview(false)}
                    className="hidden"
                  />
                </div>

                <Separator />

                <div className="space-y-4">
                  <h4 className="text-sm font-semibold">Overlays</h4>
                  <div className="grid grid-cols-2 gap-2">
                    <Button
                      variant={activeClip?.overlay?.show ? "default" : "outline"}
                      className="justify-start gap-2 h-10 px-3 transition-all"
                      onClick={() => {
                        const newOverlay = { ...activeClip?.overlay, show: !activeClip?.overlay?.show, text: activeClip?.overlay?.text || activeClip?.title };
                        const newClips = clips.map(c => c.id === activeClipId ? { ...c, overlay: newOverlay } : c);
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
                        const newClips = clips.map(c => c.id === activeClipId ? { ...c, captions: newCaptions } : c);
                        setClips(newClips);
                        if (activeClipId) saveClip(activeClipId, { captions: newCaptions });
                      }}
                    >
                      <MessageSquare className="h-4 w-4" /> Captions
                    </Button>
                  </div>

                  {/* Click Effects Selector */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <label className="text-xs text-muted-foreground flex items-center gap-1">
                        <MousePointer2 className="h-3 w-3" /> Click Effects
                      </label>
                      <select
                        value={activeClip?.click_effect || "none"}
                        onChange={(e) => {
                          const effect = e.target.value
                          const newClips = clips.map(c =>
                            c.id === activeClipId ? { ...c, click_effect: effect } : c
                          )
                          setClips(newClips)
                          if (activeClipId) saveClip(activeClipId, { click_effect: effect })
                        }}
                        className="text-[10px] py-1 px-2 rounded border bg-background"
                      >
                        <option value="none">None</option>
                        <option value="ripple">Ripple</option>
                        <option value="circle">Circle</option>
                        <option value="highlight">Highlight</option>
                      </select>
                    </div>
                    {activeClip?.click_effect && activeClip.click_effect !== "none" && (
                      <div className="text-[10px] text-muted-foreground bg-primary/5 px-2 py-1 rounded">
                        ✓ Click animations will be added at recorded click positions
                      </div>
                    )}
                  </div>

                  {/* Zoom Effect Selector */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <label className="text-xs text-muted-foreground flex items-center gap-1">
                        <Sparkles className="h-3 w-3" /> AI Zoom Effect
                      </label>
                      <select
                        value={activeClip?.zoom_effect || "none"}
                        onChange={(e) => {
                          const effect = e.target.value
                          const newClips = clips.map(c =>
                            c.id === activeClipId ? { ...c, zoom_effect: effect } : c
                          )
                          setClips(newClips)
                          if (activeClipId) saveClip(activeClipId, { zoom_effect: effect })
                        }}
                        className="text-[10px] py-1 px-2 rounded border bg-background"
                      >
                        <option value="none">None</option>
                        <option value="slow_zoom_in">Slow Zoom In</option>
                        <option value="slow_zoom_out">Slow Zoom Out</option>
                        <option value="pan_left">Pan Left</option>
                        <option value="pan_right">Pan Right</option>
                      </select>
                    </div>
                    {activeClip?.zoom_effect && activeClip.zoom_effect !== "none" && (
                      <div className="text-[10px] text-muted-foreground bg-primary/5 px-2 py-1 rounded">
                        ✓ Ken Burns effect will be applied during export
                      </div>
                    )}
                  </div>
                </div>

                {/* Text Overlay Editor */}
                <div className="space-y-4">
                  <h4 className="text-sm font-semibold">Custom Text Overlays</h4>
                  <TextOverlayEditor
                    overlays={activeClip?.overlay?.text_overlays || []}
                    onAdd={handleAddOverlay}
                    onUpdate={() => { }} // TODO: implement update
                    onRemove={handleRemoveOverlay}
                  />
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
                  <select
                    value={demo?.background_music || ""}
                    onChange={(e) => {
                      setDemo({ ...demo, background_music: e.target.value || null })
                      saveDemo({ background_music: e.target.value || null })
                    }}
                    className="w-full text-sm py-2 px-3 rounded-lg border bg-background"
                  >
                    <option value="">No music</option>
                    <option value="corporate_minimal">Corporate Minimal Tech</option>
                    <option value="upbeat_tech">Upbeat Technology</option>
                    <option value="calm_ambient">Calm Ambient</option>
                    <option value="inspiring_piano">Inspiring Piano</option>
                  </select>
                  {demo?.background_music && (
                    <div className="space-y-2">
                      <label className="text-xs text-muted-foreground">Music Volume</label>
                      <input
                        type="range"
                        min="0"
                        max="50"
                        value={(demo?.music_volume || 0.15) * 100}
                        onChange={(e) => {
                          const vol = parseInt(e.target.value) / 100
                          setDemo({ ...demo, music_volume: vol })
                          saveDemo({ music_volume: vol })
                        }}
                        className="w-full"
                      />
                    </div>
                  )}
                </div>

                <Separator />

                <div className="space-y-3">
                  <h4 className="text-sm font-semibold">Transitions</h4>
                  <div className="flex items-center justify-between">
                    <label className="text-sm">Enable clip transitions</label>
                    <Switch
                      checked={demo?.enable_transitions || false}
                      onCheckedChange={(checked) => {
                        setDemo({ ...demo, enable_transitions: checked })
                        saveDemo({ enable_transitions: checked })
                      }}
                    />
                  </div>
                  {demo?.enable_transitions && (
                    <select
                      value={demo?.transition_type || "dissolve"}
                      onChange={(e) => {
                        setDemo({ ...demo, transition_type: e.target.value })
                        saveDemo({ transition_type: e.target.value })
                      }}
                      className="w-full text-sm py-2 px-3 rounded-lg border bg-background"
                    >
                      <option value="dissolve">Dissolve</option>
                      <option value="fade">Fade</option>
                      <option value="wipe_left">Wipe Left</option>
                      <option value="wipe_right">Wipe Right</option>
                      <option value="slide_left">Slide Left</option>
                    </select>
                  )}
                </div>

                <Separator />

                <div className="space-y-2">
                  <h4 className="text-sm font-semibold">Aspect Ratio</h4>
                  <div className="grid grid-cols-3 gap-2">
                    {[
                      { id: "16:9", label: "16:9", desc: "Landscape" },
                      { id: "9:16", label: "9:16", desc: "Portrait" },
                      { id: "1:1", label: "1:1", desc: "Square" },
                    ].map((ratio) => (
                      <button
                        key={ratio.id}
                        onClick={() => {
                          setDemo({ ...demo, aspect_ratio: ratio.id })
                          saveDemo({ aspect_ratio: ratio.id })
                        }}
                        className={`p-3 rounded-lg border text-center transition-all ${(demo?.aspect_ratio || "16:9") === ratio.id
                          ? "border-primary bg-primary/10"
                          : "border-border hover:border-primary/50"
                          }`}
                      >
                        <div className="text-sm font-bold">{ratio.label}</div>
                        <div className="text-[10px] text-muted-foreground">{ratio.desc}</div>
                      </button>
                    ))}
                  </div>
                </div>

                <Separator />

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <h4 className="text-sm font-semibold">Watermark</h4>
                    <Switch
                      checked={!!demo?.watermark}
                      onCheckedChange={(checked) => {
                        const newWatermark = checked ? "AutoVidAI" : null
                        setDemo({ ...demo, watermark: newWatermark })
                        saveDemo({ watermark: newWatermark })
                      }}
                    />
                  </div>
                  {demo?.watermark && (
                    <Input
                      value={demo.watermark}
                      onChange={(e) => {
                        setDemo({ ...demo, watermark: e.target.value })
                        saveDemo({ watermark: e.target.value })
                      }}
                      placeholder="Watermark text..."
                      className="text-sm"
                    />
                  )}
                </div>

                <Separator />

                {/* Intro/Outro Section */}
                <div className="space-y-4">
                  <h4 className="text-sm font-semibold">Intro & Outro</h4>

                  {/* Intro */}
                  <div className="space-y-2 p-3 rounded-lg border bg-muted/30">
                    <div className="flex items-center justify-between">
                      <label className="text-xs font-medium">Demo Intro</label>
                      <Badge variant={demo?.has_intro ? "default" : "outline"} className="text-[10px]">
                        {demo?.has_intro ? "Generated" : "Not set"}
                      </Badge>
                    </div>
                    <Input
                      value={introTitle || demo?.title || ""}
                      onChange={(e) => setIntroTitle(e.target.value)}
                      placeholder="Title..."
                      className="text-sm"
                    />
                    <Input
                      value={introSubtitle}
                      onChange={(e) => setIntroSubtitle(e.target.value)}
                      placeholder="Subtitle (optional)..."
                      className="text-sm"
                    />
                    <Button
                      size="sm"
                      className="w-full text-xs"
                      disabled={isGeneratingIntro}
                      onClick={async () => {
                        setIsGeneratingIntro(true)
                        try {
                          const res = await fetch(`${API_URL}/api/v1/demos/${id}/intro`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                              title: introTitle || demo?.title || "Demo",
                              subtitle: introSubtitle,
                              brand_color: brandColor
                            })
                          })
                          if (res.ok) {
                            setDemo({ ...demo, has_intro: true })
                            saveDemo({ has_intro: true })
                          }
                        } catch (e) {
                          console.error('Failed to generate intro:', e)
                        } finally {
                          setIsGeneratingIntro(false)
                        }
                      }}
                    >
                      {isGeneratingIntro ? (
                        <><Loader2 className="h-3 w-3 mr-1 animate-spin" /> Generating...</>
                      ) : (
                        <><Video className="h-3 w-3 mr-1" /> Generate Intro</>
                      )}
                    </Button>
                  </div>

                  {/* Outro */}
                  <div className="space-y-2 p-3 rounded-lg border bg-muted/30">
                    <div className="flex items-center justify-between">
                      <label className="text-xs font-medium">Call-to-Action Outro</label>
                      <Badge variant={demo?.has_outro ? "default" : "outline"} className="text-[10px]">
                        {demo?.has_outro ? "Generated" : "Not set"}
                      </Badge>
                    </div>
                    <Input
                      value={outroText}
                      onChange={(e) => setOutroText(e.target.value)}
                      placeholder="CTA text..."
                      className="text-sm"
                    />
                    <Input
                      value={outroUrl}
                      onChange={(e) => setOutroUrl(e.target.value)}
                      placeholder="URL (optional)..."
                      className="text-sm"
                    />
                    <Button
                      size="sm"
                      variant="outline"
                      className="w-full text-xs"
                      disabled={isGeneratingIntro}
                      onClick={async () => {
                        setIsGeneratingIntro(true)
                        try {
                          const res = await fetch(`${API_URL}/api/v1/demos/${id}/outro`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                              title: outroText,
                              cta_text: outroText,
                              url: outroUrl
                            })
                          })
                          if (res.ok) {
                            setDemo({ ...demo, has_outro: true })
                            saveDemo({ has_outro: true })
                          }
                        } catch (e) {
                          console.error('Failed to generate outro:', e)
                        } finally {
                          setIsGeneratingIntro(false)
                        }
                      }}
                    >
                      {isGeneratingIntro ? (
                        <><Loader2 className="h-3 w-3 mr-1 animate-spin" /> Generating...</>
                      ) : (
                        <><Video className="h-3 w-3 mr-1" /> Generate Outro</>
                      )}
                    </Button>
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
