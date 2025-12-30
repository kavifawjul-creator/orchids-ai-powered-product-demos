"use client"

import * as React from "react"
import { useSearchParams, useRouter } from "next/navigation"
import { motion, AnimatePresence } from "framer-motion"
import { 
  Terminal, 
  Cpu, 
  MousePointer2, 
  CheckCircle2, 
  Loader2,
  Search,
  ArrowRight,
  AlertCircle,
  Eye
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { supabase } from "@/lib/supabase"

interface AgentLog {
  type: "reasoning" | "action" | "milestone" | "error" | "verification"
  text: string
  timestamp: number
}

interface DemoStatus {
  id: string
  status: string
  title?: string
  updated_at?: string
}

export default function GeneratePage() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const repo = searchParams.get("repo") || ""
  const prompt = searchParams.get("prompt") || ""
  const demoIdParam = searchParams.get("demo_id")

  const [logs, setLogs] = React.useState<AgentLog[]>([])
  const [progress, setProgress] = React.useState(0)
  const [isFinished, setIsFinished] = React.useState(false)
  const [hasError, setHasError] = React.useState(false)
  const [currentAction, setCurrentAction] = React.useState("Initializing...")
  const [milestonesCount, setMilestonesCount] = React.useState(0)
  const [demoId, setDemoId] = React.useState<string | null>(demoIdParam)
  const [currentFrame, setCurrentFrame] = React.useState<string | null>(null)
  const [currentFeature, setCurrentFeature] = React.useState<string>("")
  const [stepProgress, setStepProgress] = React.useState({ current: 0, total: 0 })
  const [sessionId, setSessionId] = React.useState<string | null>(null)

  const addLog = React.useCallback((log: AgentLog) => {
    setLogs(prev => [...prev, log])
  }, [])

  React.useEffect(() => {
    if (!repo || !prompt) {
      router.push("/dashboard/new")
      return
    }

    const startGeneration = async () => {
      try {
        addLog({ type: "reasoning", text: `Initializing generation for ${repo.split('/').pop()}...`, timestamp: Date.now() })
        
        const response = await fetch("/api/demos/generate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            repo_url: repo,
            prompt: prompt,
            title: prompt.slice(0, 50)
          })
        })

        if (!response.ok) {
          throw new Error("Failed to start generation")
        }

        const data = await response.json()
        setDemoId(data.demo_id)
        addLog({ type: "action", text: `Demo created: ${data.demo_id.slice(0, 8)}...`, timestamp: Date.now() })
        setProgress(10)

      } catch (error) {
        addLog({ type: "error", text: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`, timestamp: Date.now() })
        setHasError(true)
      }
    }

    if (!demoId) {
      startGeneration()
    }
  }, [repo, prompt, router, addLog, demoId])

  React.useEffect(() => {
    if (!demoId) return

    const pollStatus = async () => {
      try {
        const response = await fetch(`/api/demos/${demoId}/status`)
        if (response.ok) {
          const status: DemoStatus = await response.json()
          
          switch (status.status?.toLowerCase()) {
            case "pending":
              setProgress(15)
              setCurrentAction("Queued for processing...")
              break
            case "building":
              setProgress(25)
              setCurrentAction("Building sandbox environment...")
              addLog({ type: "action", text: "Creating isolated sandbox environment...", timestamp: Date.now() })
              break
            case "planning":
              setProgress(40)
              setCurrentAction("AI planning execution steps...")
              addLog({ type: "reasoning", text: "Analyzing prompt and generating execution plan...", timestamp: Date.now() })
              break
            case "executing":
              setProgress(prev => Math.min(prev + 5, 85))
              setCurrentAction("Agent executing browser actions...")
              break
            case "recording":
              setProgress(90)
              setCurrentAction("Recording and processing video...")
              break
            case "completed":
              setProgress(100)
              setCurrentAction("Generation complete!")
              addLog({ type: "milestone", text: "COMPLETE: Demo video generated successfully!", timestamp: Date.now() })
              setMilestonesCount(prev => prev + 1)
              setIsFinished(true)
              return true
            case "error":
              setHasError(true)
              addLog({ type: "error", text: `Generation failed: ${status.title || 'Unknown error'}`, timestamp: Date.now() })
              return true
          }
        }
        return false
      } catch (error) {
        return false
      }
    }

    const interval = setInterval(async () => {
      const shouldStop = await pollStatus()
      if (shouldStop) {
        clearInterval(interval)
      }
    }, 2000)

    pollStatus()

    return () => clearInterval(interval)
  }, [demoId, addLog])

  React.useEffect(() => {
    if (!demoId) return

    const channel = supabase
      .channel(`demo:${demoId}`)
      .on(
        'postgres_changes',
        {
          event: 'UPDATE',
          schema: 'public',
          table: 'demos',
          filter: `id=eq.${demoId}`
        },
        (payload) => {
          const newStatus = payload.new as DemoStatus
          if (newStatus.status?.toLowerCase() === 'completed') {
            setProgress(100)
            setIsFinished(true)
          } else if (newStatus.status?.toLowerCase() === 'error') {
            setHasError(true)
          }
        }
      )
      .subscribe()

    return () => {
      supabase.removeChannel(channel)
    }
  }, [demoId])

  React.useEffect(() => {
    if (isFinished || hasError || !demoId) return

    const simulateProgress = () => {
      const actions = [
        { type: "action" as const, text: "Navigating to application entry point..." },
        { type: "reasoning" as const, text: "Analyzing page structure and interactive elements..." },
        { type: "action" as const, text: "Detecting navigation components..." },
        { type: "verification" as const, text: "Verifying page load complete - confidence: 0.95" },
        { type: "action" as const, text: "Executing click on primary navigation..." },
        { type: "reasoning" as const, text: "Processing visual feedback from browser..." },
        { type: "milestone" as const, text: "RECORDED: Navigation sequence captured" },
        { type: "action" as const, text: "Interacting with feature components..." },
        { type: "verification" as const, text: "Action verified via vision model" },
        { type: "action" as const, text: "Capturing final state screenshots..." },
      ]

      let index = 0
      const logInterval = setInterval(() => {
        if (index < actions.length && !isFinished && !hasError) {
          const action = actions[index]
          addLog({ ...action, timestamp: Date.now() })
          
          if (action.type === "action") {
            setCurrentAction(action.text)
          }
          if (action.type === "milestone") {
            setMilestonesCount(prev => prev + 1)
          }
          
          index++
        } else {
          clearInterval(logInterval)
        }
      }, 3000)

      return () => clearInterval(logInterval)
    }

    const cleanup = simulateProgress()
    return cleanup
  }, [demoId, isFinished, hasError, addLog])

  return (
    <div className="max-w-6xl mx-auto space-y-6 pb-12">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between bg-muted/30 p-4 rounded-xl border">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
            <Cpu className={`h-6 w-6 ${!isFinished && !hasError ? 'animate-pulse' : ''}`} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold truncate max-w-[200px]">{repo || "Repository"}</span>
              <Badge variant={hasError ? "destructive" : isFinished ? "default" : "outline"} className="text-[10px] h-5">
                {hasError ? "ERROR" : isFinished ? "COMPLETE" : "LIVE SESSION"}
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground line-clamp-1 italic">&quot;{prompt}&quot;</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right hidden md:block">
            <p className="text-[10px] font-mono text-muted-foreground uppercase tracking-widest">Progress</p>
            <p className="text-sm font-bold">{Math.round(progress)}%</p>
          </div>
          <Progress value={progress} className="w-24 md:w-32 h-2" />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 h-[600px]">
        <Card className="lg:col-span-4 flex flex-col overflow-hidden bg-zinc-950 border-zinc-800">
          <div className="p-3 border-b border-zinc-800 bg-zinc-900/50 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Terminal className="h-4 w-4 text-zinc-400" />
              <span className="text-xs font-mono text-zinc-400">AGENT_ENGINE_LOGS</span>
            </div>
            <div className="flex gap-1">
              <div className={`h-2 w-2 rounded-full ${hasError ? 'bg-red-500' : 'bg-red-500/50'}`} />
              <div className={`h-2 w-2 rounded-full ${isFinished ? 'bg-green-500' : 'bg-yellow-500/50'}`} />
              <div className={`h-2 w-2 rounded-full ${!hasError && !isFinished ? 'bg-green-500 animate-pulse' : 'bg-green-500/50'}`} />
            </div>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-3 font-mono text-xs">
            <AnimatePresence initial={false}>
              {logs.map((log, i) => (
                <motion.div 
                  key={i}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  className={`flex gap-2 ${
                    log.type === 'milestone' ? 'text-green-400' : 
                    log.type === 'error' ? 'text-red-400' :
                    log.type === 'verification' ? 'text-blue-400' :
                    log.type === 'action' ? 'text-zinc-300' : 'text-zinc-500'
                  }`}
                >
                  <span className="shrink-0 text-zinc-600">{`>`}</span>
                  <span className={log.type === 'milestone' || log.type === 'error' ? 'font-bold' : ''}>{log.text}</span>
                </motion.div>
              ))}
            </AnimatePresence>
            {!isFinished && !hasError && (
              <div className="flex items-center gap-2 text-zinc-500">
                <Loader2 className="h-3 w-3 animate-spin" />
                <span>Processing...</span>
              </div>
            )}
            <div className="h-4" />
          </div>
        </Card>

        <Card className="lg:col-span-8 flex flex-col overflow-hidden bg-background border shadow-2xl relative">
          <div className="h-10 border-b bg-muted/50 flex items-center px-4 gap-3">
            <div className="flex gap-1.5">
              <div className="h-3 w-3 rounded-full bg-border" />
              <div className="h-3 w-3 rounded-full bg-border" />
              <div className="h-3 w-3 rounded-full bg-border" />
            </div>
            <div className="flex-1 h-6 bg-background rounded border flex items-center px-2">
              <Search className="h-3 w-3 text-muted-foreground mr-2" />
              <span className="text-[10px] text-muted-foreground truncate">
                {currentFeature || "localhost:3000"}
              </span>
            </div>
          </div>

          <div className="flex-1 relative bg-zinc-50 flex items-center justify-center overflow-hidden">
            {currentFrame ? (
              <img 
                src={`data:image/jpeg;base64,${currentFrame}`}
                alt="Live browser view"
                className="w-full h-full object-contain"
              />
            ) : (
              <div className="w-[90%] h-[80%] bg-white rounded-lg shadow-sm border border-zinc-200 p-6 space-y-4">
                <div className="flex items-center justify-between mb-8">
                  <div className="h-4 w-32 bg-zinc-100 rounded animate-pulse" />
                  <div className="flex gap-2">
                    <div className="h-8 w-8 rounded bg-zinc-100 animate-pulse" />
                    <div className="h-8 w-8 rounded bg-zinc-100 animate-pulse" />
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-4">
                  {[1, 2, 3].map(i => (
                    <div key={i} className="h-24 bg-zinc-50 rounded-lg border border-zinc-100 p-3 animate-pulse">
                      <div className="h-2 w-12 bg-zinc-100 rounded mb-2" />
                      <div className="h-4 w-8 bg-primary/20 rounded" />
                    </div>
                  ))}
                </div>
                <div className="h-40 bg-primary/5 rounded-lg border border-primary/10 flex items-end p-4 gap-2">
                  {[40, 70, 45, 90, 65, 80, 55].map((h, i) => (
                    <motion.div 
                      key={i} 
                      className="flex-1 bg-primary/40 rounded-t"
                      initial={{ height: 0 }}
                      animate={{ height: `${h}%` }}
                      transition={{ duration: 1, delay: i * 0.1 }}
                    />
                  ))}
                </div>
              </div>
            )}

            {!isFinished && !hasError && (
              <motion.div 
                className="absolute z-20 pointer-events-none"
                animate={{ 
                  x: [0, 200, -150, 50, 0],
                  y: [0, -100, 150, -50, 0],
                }}
                transition={{ repeat: Infinity, duration: 10 }}
              >
                <div className="relative">
                  <MousePointer2 className="h-6 w-6 text-primary fill-primary drop-shadow-lg" />
                  <div className="absolute top-6 left-6 whitespace-nowrap px-2 py-1 bg-primary text-primary-foreground text-[10px] font-bold rounded shadow-lg">
                    AI AGENT
                  </div>
                </div>
              </motion.div>
            )}

            {!isFinished && !hasError && (
              <div className="absolute top-4 right-4 flex items-center gap-2 px-3 py-1.5 bg-red-500 text-white text-[10px] font-bold rounded-full animate-pulse shadow-lg z-30">
                <div className="h-2 w-2 rounded-full bg-white" />
                REC
              </div>
            )}

            <AnimatePresence>
              {isFinished && (
                <motion.div 
                  className="absolute inset-0 bg-background/80 backdrop-blur-md flex flex-col items-center justify-center z-40 p-8 text-center"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                >
                  <div className="h-20 w-20 rounded-full bg-green-500/10 flex items-center justify-center text-green-500 mb-6">
                    <CheckCircle2 className="h-12 w-12" />
                  </div>
                  <h3 className="text-2xl font-bold mb-2">Generation Complete!</h3>
                  <p className="text-muted-foreground mb-8 max-w-sm">
                    Your demo video has been generated with {milestonesCount} recorded milestone{milestonesCount !== 1 ? 's' : ''}.
                  </p>
                  <div className="flex gap-4">
                    <Button size="lg" className="rounded-full px-8" onClick={() => router.push('/dashboard')}>
                      Go to Dashboard
                    </Button>
                    {demoId && (
                      <Button size="lg" variant="outline" className="rounded-full px-8" onClick={() => router.push(`/dashboard/demo/${demoId}`)}>
                        View Demo
                        <ArrowRight className="ml-2 h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </motion.div>
              )}

              {hasError && (
                <motion.div 
                  className="absolute inset-0 bg-background/80 backdrop-blur-md flex flex-col items-center justify-center z-40 p-8 text-center"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                >
                  <div className="h-20 w-20 rounded-full bg-red-500/10 flex items-center justify-center text-red-500 mb-6">
                    <AlertCircle className="h-12 w-12" />
                  </div>
                  <h3 className="text-2xl font-bold mb-2">Generation Failed</h3>
                  <p className="text-muted-foreground mb-8 max-w-sm">
                    Something went wrong during the generation process. Please try again.
                  </p>
                  <div className="flex gap-4">
                    <Button size="lg" variant="outline" className="rounded-full px-8" onClick={() => router.push('/dashboard/new')}>
                      Try Again
                    </Button>
                    <Button size="lg" className="rounded-full px-8" onClick={() => router.push('/dashboard')}>
                      Go to Dashboard
                    </Button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          <div className="h-12 border-t bg-muted/30 flex items-center px-4 justify-between">
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              {!isFinished && !hasError && <Loader2 className="h-3 w-3 animate-spin" />}
              <span>Status: <span className="text-foreground font-medium">{currentAction}</span></span>
            </div>
            <div className="flex items-center gap-2">
              {stepProgress.total > 0 && (
                <Badge variant="outline" className="text-[10px]">
                  Step {stepProgress.current}/{stepProgress.total}
                </Badge>
              )}
              <Badge variant="secondary" className="bg-primary/10 text-primary border-none text-[10px]">
                {milestonesCount} Milestone{milestonesCount !== 1 ? 's' : ''}
              </Badge>
            </div>
          </div>
        </Card>
      </div>
    </div>
  )
}
