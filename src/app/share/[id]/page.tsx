
import { useState, useEffect, useRef } from "react"
import { useParams } from "next/navigation"
import { motion, AnimatePresence } from "framer-motion"
import { 
  Play, 
  Pause, 
  SkipBack, 
  SkipForward, 
  Settings, 
  Video,
  Zap,
  Globe,
  Share2,
  ExternalLink,
  Github,
  Loader2,
  MousePointer2,
  Download,
  Volume2,
  VolumeX,
  Maximize
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"
import Link from "next/link"
import { supabase } from "@/lib/supabase"

export default function SharePage() {
  const { id } = useParams()
  const [demo, setDemo] = useState<any>(null)
  const [clips, setClips] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [isPlaying, setIsPlaying] = useState(false)
  const [activeClipIndex, setActiveClipIndex] = useState(0)
  const [progress, setProgress] = useState(0)
  const [isMuted, setIsMuted] = useState(false)
  const videoRef = useRef<HTMLVideoElement>(null)

  useEffect(() => {
    async function fetchData() {
      const { data: demoData } = await supabase
        .from('demos')
        .select('*')
        .eq('id', id)
        .single()
      
      if (demoData) {
        setDemo(demoData)
        // Track view
        fetch("/api/analytics/track", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            demo_id: id,
            event_type: "view",
            metadata: { referrer: document.referrer }
          })
        }).catch(console.error)
      }

      const { data: clipsData } = await supabase
        .from('clips')
        .select('*')
        .eq('demo_id', id)
        .order('order_index', { ascending: true })
      
      if (clipsData) setClips(clipsData)
      setLoading(false)
    }
    fetchData()
  }, [id])

  const activeClip = clips[activeClipIndex]
  const hasFullVideo = demo?.video_url

  useEffect(() => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.play().catch(() => setIsPlaying(false))
      } else {
        videoRef.current.pause()
      }
    }
  }, [isPlaying])

  useEffect(() => {
    let interval: any
    if (isPlaying && clips.length > 0 && !hasFullVideo) {
      interval = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 100) {
            if (activeClipIndex < clips.length - 1) {
              setActiveClipIndex(activeClipIndex + 1)
              return 0
            } else {
              setIsPlaying(false)
              return 100
            }
          }
          return prev + 1 
        })
      }, 100)
    }
    return () => clearInterval(interval)
  }, [isPlaying, activeClipIndex, clips, hasFullVideo])

  const handleTimeUpdate = () => {
    if (videoRef.current && hasFullVideo) {
      const p = (videoRef.current.currentTime / videoRef.current.duration) * 100
      setProgress(p)
    }
  }

  const handleVideoEnded = () => {
    if (!hasFullVideo && activeClipIndex < clips.length - 1) {
      setActiveClipIndex(activeClipIndex + 1)
      setProgress(0)
    } else {
      setIsPlaying(false)
    }
  }

  if (loading) {
    return <div className="min-h-screen bg-black flex items-center justify-center">
      <Loader2 className="h-8 w-8 animate-spin text-primary" />
    </div>
  }

  if (!demo || clips.length === 0) {
    return <div className="min-h-screen bg-black flex items-center justify-center text-white">
      Demo not found or empty
    </div>
  }

  const currentMediaUrl = hasFullVideo ? demo.video_url : activeClip?.video_url

  return (
    <div className="min-h-screen bg-black text-white selection:bg-primary selection:text-white">
      {/* Navigation */}
      <nav className="border-b border-white/10 px-6 py-4 flex items-center justify-between backdrop-blur-md bg-black/50 sticky top-0 z-50">
        <div className="flex items-center gap-2">
          <Link href="/" className="flex items-center gap-2">
            <div className="bg-primary p-1.5 rounded-lg shadow-lg shadow-primary/20">
              <Video className="h-5 w-5 text-white" />
            </div>
            <span className="font-bold text-lg tracking-tight">AutoVid AI</span>
          </Link>
        </div>
        <div className="flex items-center gap-4">
          <Link href="/dashboard/new">
            <Button variant="ghost" className="text-white/70 hover:text-white hover:bg-white/10 hidden sm:flex">
              Create Your Own
            </Button>
          </Link>
          <Button className="bg-white text-black hover:bg-white/90 shadow-xl shadow-white/10 font-bold rounded-full px-6">
            Get Started Free
          </Button>
        </div>
      </nav>

      <main className="max-w-6xl mx-auto px-6 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
          {/* Player Section */}
          <div className="lg:col-span-8 space-y-8">
            <div className="relative group">
              <div className="absolute -inset-1 bg-gradient-to-r from-primary/50 to-blue-500/50 rounded-[2rem] blur-2xl opacity-20 group-hover:opacity-30 transition-opacity" />
              <Card className="relative overflow-hidden bg-zinc-950 border-white/10 shadow-2xl rounded-[1.5rem] aspect-video">
                <AnimatePresence mode="wait">
                  {currentMediaUrl ? (
                    <motion.video
                      key={currentMediaUrl}
                      ref={videoRef}
                      src={currentMediaUrl}
                      className="w-full h-full object-cover"
                      onTimeUpdate={handleTimeUpdate}
                      onEnded={handleVideoEnded}
                      muted={isMuted}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                    />
                  ) : (
                    <motion.div
                      key={activeClipIndex}
                      initial={{ opacity: 0, scale: 1.1 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.9 }}
                      transition={{ duration: 0.6 }}
                      className="absolute inset-0"
                    >
                      <img 
                        src={activeClip.thumbnail_url} 
                        alt={activeClip.title} 
                        className="w-full h-full object-cover opacity-80"
                      />
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Overlays */}
                <AnimatePresence>
                  {activeClip.overlay?.show && (
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

                {activeClip.captions && isPlaying && (
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

                {/* Overlay UI */}
                <div className="absolute inset-0 flex flex-col justify-between p-6 z-10 pointer-events-none">
                  <div className="flex justify-between items-start pointer-events-auto">
                    <Badge className="bg-black/60 backdrop-blur-md border-white/10 text-white/90 text-[10px] uppercase tracking-widest px-3 py-1">
                      <Globe className="h-3 w-3 mr-1.5 inline" /> Public Demo
                    </Badge>
                    <Badge variant="outline" className="border-primary/50 text-primary bg-primary/10 backdrop-blur-md">
                      AI Generated
                    </Badge>
                  </div>

                  {!isPlaying && (
                    <motion.button 
                      whileHover={{ scale: 1.1 }}
                      whileTap={{ scale: 0.9 }}
                      onClick={() => setIsPlaying(true)}
                      className="self-center bg-white/20 hover:bg-white/30 backdrop-blur-xl border border-white/30 rounded-full p-8 shadow-2xl group/play transition-all pointer-events-auto"
                    >
                      <Play className="h-12 w-12 text-white fill-white transition-transform group-hover/play:scale-110" />
                    </motion.button>
                  )}

                  <div className="space-y-4 pointer-events-auto">
                    {/* Progress Bar */}
                    <div className="h-1.5 w-full bg-white/10 rounded-full overflow-hidden cursor-pointer backdrop-blur-sm group/progress">
                      <motion.div 
                        className="h-full relative" 
                        style={{ backgroundColor: demo.brand_color || "#7c3aed", boxShadow: `0 0 15px ${demo.brand_color || "#7c3aed"}80` }}
                        animate={{ width: `${progress}%` }}
                        transition={{ duration: 0.1 }}
                      >
                         <div className="absolute right-0 top-1/2 -translate-y-1/2 w-3 h-3 bg-white rounded-full scale-0 group-hover/progress:scale-100 transition-transform" />
                      </motion.div>
                    </div>
                    
                    {/* Controls */}
                    <div className="flex items-center justify-between text-white/80">
                      <div className="flex items-center gap-4">
                        <button className="hover:text-white transition-colors">
                          <SkipBack className="h-5 w-5 fill-current" />
                        </button>
                        <button 
                          onClick={() => setIsPlaying(!isPlaying)}
                          className="bg-white text-black p-2.5 rounded-full hover:scale-105 transition-transform"
                        >
                          {isPlaying ? <Pause className="h-5 w-5 fill-current" /> : <Play className="h-5 w-5 fill-current" />}
                        </button>
                        <button className="hover:text-white transition-colors">
                          <SkipForward className="h-5 w-5 fill-current" />
                        </button>
                        <div className="flex items-center gap-2">
                           <button onClick={() => setIsMuted(!isMuted)} className="hover:text-white transition-colors">
                             {isMuted ? <VolumeX className="h-5 w-5" /> : <Volume2 className="h-5 w-5" />}
                           </button>
                        </div>
                        <span className="text-sm font-mono tracking-tighter ml-2">
                          {hasFullVideo && videoRef.current ? 
                            `${Math.floor(videoRef.current.currentTime / 60)}:${Math.floor(videoRef.current.currentTime % 60).toString().padStart(2, '0')}` : 
                            `0:${Math.floor(progress / 5).toString().padStart(2, '0')}`
                          } / {hasFullVideo && videoRef.current ? 
                            `${Math.floor(videoRef.current.duration / 60)}:${Math.floor(videoRef.current.duration % 60).toString().padStart(2, '0')}` : 
                            activeClip.duration
                          }
                        </span>
                      </div>
                      <div className="flex items-center gap-4">
                         <div className="flex items-center gap-1.5 text-[10px] font-bold bg-white/5 px-2 py-1 rounded border border-white/10">
                           <div className="h-2 w-2 rounded-full bg-primary animate-pulse" />
                           {hasFullVideo ? "4K MASTER" : "HD PREVIEW"}
                         </div>
                        <button className="hover:text-white transition-colors">
                          <Maximize className="h-5 w-5" />
                        </button>
                        <button className="hover:text-white transition-colors">
                          <Settings className="h-5 w-5" />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Autonomous Agent Cursor */}
                {isPlaying && !hasFullVideo && (
                  <motion.div 
                    className="absolute z-20 pointer-events-none"
                    animate={{ 
                      x: [150, 450, 250, 550, 150],
                      y: [120, 250, 450, 180, 120],
                    }}
                    transition={{ repeat: Infinity, duration: 8, ease: "easeInOut" }}
                  >
                    <MousePointer2 className="h-10 w-10 text-primary fill-primary drop-shadow-[0_0_15px_rgba(124,58,237,0.8)]" />
                  </motion.div>
                )}
              </Card>
            </div>

            {/* Info Section */}
            <div className="space-y-6">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="space-y-2">
                  <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight">{demo.title}</h1>
                  <div className="flex items-center gap-4 text-white/50 text-sm font-medium">
                    <span className="flex items-center gap-1.5">
                      <Zap className="h-4 w-4 text-yellow-500" /> {demo.author || "AutoVid AI"}
                    </span>
                    <span>•</span>
                    <span>1.2k views</span>
                    <span>•</span>
                    <span>{new Date(demo.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Button variant="outline" className="border-white/10 bg-white/5 hover:bg-white/10 rounded-full gap-2 px-6">
                    <Share2 className="h-4 w-4" /> Share
                  </Button>
                  {hasFullVideo && (
                    <a href={demo.video_url} download target="_blank">
                      <Button variant="outline" className="border-white/10 bg-white/5 hover:bg-white/10 rounded-full gap-2 px-6">
                        <Download className="h-4 w-4" /> Download
                      </Button>
                    </a>
                  )}
                  <Button className="bg-primary hover:bg-primary/90 rounded-full gap-2 px-6 shadow-lg shadow-primary/20">
                    <Github className="h-4 w-4" /> Source Code
                  </Button>
                </div>
              </div>

              <div className="h-[1px] w-full bg-white/10" />

              <div className="space-y-4">
                <p className="text-lg text-white/70 leading-relaxed max-w-3xl">
                  {demo.description || "No description provided for this autonomous demo."}
                </p>
                <div className="flex items-center gap-2 font-mono text-xs text-primary bg-primary/10 w-fit px-3 py-1 rounded-full border border-primary/20">
                  <ExternalLink className="h-3 w-3" />
                  {demo.repo_url}
                </div>
              </div>
            </div>
          </div>

          {/* Sidebar Section */}
          <div className="lg:col-span-4 space-y-8">
            <div className="space-y-4">
              <h3 className="text-lg font-bold flex items-center gap-2">
                <span className="h-6 w-1 bg-primary rounded-full" />
                Demo Breakdown
              </h3>
              <div className="space-y-3">
                {clips.map((clip, index) => (
                  <button 
                    key={clip.id}
                    onClick={() => {
                      setActiveClipIndex(index)
                      setProgress(0)
                      setIsPlaying(true)
                      if (hasFullVideo && videoRef.current) {
                        // In a real app, we'd map clip start times to the full video
                        // For now, let's just show the clip
                      }
                    }}
                    className={`w-full text-left group transition-all p-3 rounded-2xl border ${activeClipIndex === index ? 'bg-primary/10 border-primary/50' : 'bg-white/5 border-transparent hover:bg-white/10'}`}
                  >
                    <div className="flex gap-4">
                      <div className="relative w-24 aspect-video rounded-lg overflow-hidden flex-shrink-0">
                        <img src={clip.thumbnail_url} alt={clip.title} className="w-full h-full object-cover" />
                        <div className="absolute bottom-1 right-1 bg-black/80 px-1 rounded text-[10px] font-mono">
                          {clip.duration}
                        </div>
                      </div>
                      <div className="space-y-1 py-1">
                        <p className={`text-sm font-bold leading-tight ${activeClipIndex === index ? 'text-primary' : 'text-white'}`}>
                          {index + 1}. {clip.title}
                        </p>
                        <p className="text-[10px] text-white/40 uppercase tracking-widest font-bold">Autonomous Recording</p>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            <Card className="bg-gradient-to-br from-primary/20 to-blue-600/20 border-primary/30 p-6 rounded-[2rem] space-y-4 shadow-2xl shadow-primary/10">
              <div className="space-y-2">
                <h4 className="text-xl font-bold">Build like this.</h4>
                <p className="text-sm text-white/70">
                  Create high-fidelity autonomous product demos from your codebase in minutes. No recording required.
                </p>
              </div>
              <Link href="/dashboard/new" className="block">
                <Button className="w-full bg-white text-black hover:bg-white/90 font-bold rounded-xl py-6">
                  Try AutoVid AI Free
                </Button>
              </Link>
            </Card>
          </div>
        </div>
      </main>

      <footer className="border-t border-white/10 mt-24 py-12 px-6">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row justify-between items-center gap-8">
          <div className="flex items-center gap-2 opacity-50">
            <Video className="h-5 w-5" />
            <span className="font-bold tracking-tight">AutoVid AI</span>
          </div>
          <div className="flex gap-8 text-sm text-white/40 font-medium">
            <a href="#" className="hover:text-white transition-colors">Privacy</a>
            <a href="#" className="hover:text-white transition-colors">Terms</a>
            <a href="#" className="hover:text-white transition-colors">Twitter</a>
            <a href="#" className="hover:text-white transition-colors">GitHub</a>
          </div>
          <p className="text-xs text-white/20 font-mono">© 2024 AUTOVID ENGINE v0.4.2</p>
        </div>
      </footer>
    </div>
  )
}
