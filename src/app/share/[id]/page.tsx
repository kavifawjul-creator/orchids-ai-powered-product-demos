
"use client"

import { useState, useEffect } from "react"
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
  Github
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"
import Link from "next/link"

const demoData = {
  title: "Onboarding Flow Walkthrough",
  repo: "acme-app-frontend",
  description: "A complete walkthrough of the user onboarding process, from signup to the first dashboard view. This demo was generated autonomously by analyzing the codebase.",
  author: "Acme Engineering",
  views: "1.2k",
  date: "2 days ago",
  brandColor: "#7c3aed",
  clips: [
    {
      id: "clip-1",
      title: "Introduction & Login",
      duration: "0:12",
      thumbnail: "https://images.unsplash.com/photo-1614332287897-cdc485fa562d?w=800&h=450&fit=crop",
    },
    {
      id: "clip-2",
      title: "Analytics Dashboard Overview",
      duration: "0:45",
      thumbnail: "https://images.unsplash.com/photo-1551288049-bbda3865c170?w=800&h=450&fit=crop",
    },
    {
      id: "clip-3",
      title: "Custom Report Generation",
      duration: "1:15",
      thumbnail: "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=800&h=450&fit=crop",
    }
  ]
}

export default function SharePage() {
  const { id } = useParams()
  const [isPlaying, setIsPlaying] = useState(false)
  const [activeClipIndex, setActiveClipIndex] = useState(0)
  const [progress, setProgress] = useState(0)

  const activeClip = demoData.clips[activeClipIndex]

  useEffect(() => {
    let interval: any
    if (isPlaying) {
      interval = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 100) {
            if (activeClipIndex < demoData.clips.length - 1) {
              setActiveClipIndex(activeClipIndex + 1)
              return 0
            } else {
              setIsPlaying(false)
              return 100
            }
          }
          return prev + 0.5
        })
      }, 50)
    }
    return () => clearInterval(interval)
  }, [isPlaying, activeClipIndex])

  return (
    <div className="min-h-screen bg-black text-white selection:bg-primary selection:text-white">
      {/* Navigation */}
      <nav className="border-b border-white/10 px-6 py-4 flex items-center justify-between backdrop-blur-md bg-black/50 sticky top-0 z-50">
        <div className="flex items-center gap-2">
          <div className="bg-primary p-1.5 rounded-lg shadow-lg shadow-primary/20">
            <Video className="h-5 w-5 text-white" />
          </div>
          <span className="font-bold text-lg tracking-tight">AutoVid AI</span>
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
                  <motion.div
                    key={activeClipIndex}
                    initial={{ opacity: 0, scale: 1.1 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.9 }}
                    transition={{ duration: 0.6 }}
                    className="absolute inset-0"
                  >
                    <img 
                      src={activeClip.thumbnail} 
                      alt={activeClip.title} 
                      className="w-full h-full object-cover opacity-80"
                    />
                  </motion.div>
                </AnimatePresence>

                {/* Overlay UI */}
                <div className="absolute inset-0 flex flex-col justify-between p-6 z-10">
                  <div className="flex justify-between items-start">
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
                      className="self-center bg-white/20 hover:bg-white/30 backdrop-blur-xl border border-white/30 rounded-full p-8 shadow-2xl group/play transition-all"
                    >
                      <Play className="h-12 w-12 text-white fill-white transition-transform group-hover/play:scale-110" />
                    </motion.button>
                  )}

                  <div className="space-y-4">
                    {/* Progress Bar */}
                    <div className="h-1.5 w-full bg-white/10 rounded-full overflow-hidden cursor-pointer backdrop-blur-sm">
                      <motion.div 
                        className="h-full bg-primary shadow-[0_0_15px_rgba(124,58,237,0.5)]" 
                        animate={{ width: `${progress}%` }}
                        transition={{ duration: 0.1 }}
                      />
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
                        <span className="text-sm font-mono tracking-tighter ml-2">
                          {Math.floor(progress / 20)}:{(Math.floor(progress % 20)).toString().padStart(2, '0')} / 2:12
                        </span>
                      </div>
                      <div className="flex items-center gap-4">
                         <div className="flex items-center gap-1.5 text-[10px] font-bold bg-white/5 px-2 py-1 rounded border border-white/10">
                           <div className="h-2 w-2 rounded-full bg-primary animate-pulse" />
                           HD PREVIEW
                         </div>
                        <button className="hover:text-white transition-colors">
                          <Settings className="h-5 w-5" />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Autonomous Agent Cursor */}
                {isPlaying && (
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
                  <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight">{demoData.title}</h1>
                  <div className="flex items-center gap-4 text-white/50 text-sm font-medium">
                    <span className="flex items-center gap-1.5">
                      <Zap className="h-4 w-4 text-yellow-500" /> {demoData.author}
                    </span>
                    <span>•</span>
                    <span>{demoData.views} views</span>
                    <span>•</span>
                    <span>{demoData.date}</span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Button variant="outline" className="border-white/10 bg-white/5 hover:bg-white/10 rounded-full gap-2 px-6">
                    <Share2 className="h-4 w-4" /> Share
                  </Button>
                  <Button className="bg-primary hover:bg-primary/90 rounded-full gap-2 px-6 shadow-lg shadow-primary/20">
                    <Github className="h-4 w-4" /> Source Code
                  </Button>
                </div>
              </div>

              <Separator className="bg-white/10" />

              <div className="space-y-4">
                <p className="text-lg text-white/70 leading-relaxed max-w-3xl">
                  {demoData.description}
                </p>
                <div className="flex items-center gap-2 font-mono text-xs text-primary bg-primary/10 w-fit px-3 py-1 rounded-full border border-primary/20">
                  <ExternalLink className="h-3 w-3" />
                  github.com/{demoData.repo}
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
                {demoData.clips.map((clip, index) => (
                  <button 
                    key={clip.id}
                    onClick={() => {
                      setActiveClipIndex(index)
                      setProgress(0)
                      setIsPlaying(true)
                    }}
                    className={`w-full text-left group transition-all p-3 rounded-2xl border ${activeClipIndex === index ? 'bg-primary/10 border-primary/50' : 'bg-white/5 border-transparent hover:bg-white/10'}`}
                  >
                    <div className="flex gap-4">
                      <div className="relative w-24 aspect-video rounded-lg overflow-hidden flex-shrink-0">
                        <img src={clip.thumbnail} alt={clip.title} className="w-full h-full object-cover" />
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

function Separator({ className }: { className?: string }) {
  return <div className={`h-[1px] w-full ${className}`} />
}
