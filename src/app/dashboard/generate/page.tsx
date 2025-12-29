
"use client"

import * as React from "react"
import { useSearchParams, useRouter } from "next/navigation"
import { motion, AnimatePresence } from "framer-motion"
import { 
  Terminal, 
  Monitor, 
  Cpu, 
  Zap, 
  MousePointer2, 
  CheckCircle2, 
  Loader2,
  Video,
  ExternalLink,
  GitBranch,
  Search,
  ArrowRight
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"

const simulationSteps = [
  { type: "reasoning", text: "Analyzing repository structure...", delay: 1000 },
  { type: "action", text: "Detected Next.js framework. Identifying routes...", delay: 2000 },
  { type: "reasoning", text: "Found primary entry point at /dashboard.", delay: 3000 },
  { type: "action", text: "Starting browser session at http://localhost:3000/dashboard", delay: 4000 },
  { type: "reasoning", text: "Locating 'Analytics' tab as requested in prompt.", delay: 5500 },
  { type: "action", text: "Interaction: Hovering over navigation sidebar.", delay: 7000 },
  { type: "action", text: "Interaction: Clicking on 'Analytics' menu item.", delay: 8500 },
  { type: "milestone", text: "RECORDED: Navigation to Analytics flow.", delay: 10000 },
  { type: "reasoning", text: "Identifying charts and data visualization components.", delay: 11500 },
  { type: "action", text: "Interaction: Dragging date range selector to 'Last 30 Days'.", delay: 13000 },
  { type: "milestone", text: "RECORDED: Date range interaction.", delay: 15000 },
  { type: "reasoning", text: "Finalizing demo recording and stitching clips.", delay: 17000 },
]

export default function GeneratePage() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const repo = searchParams.get("repo") || "github.com/acme/app"
  const prompt = searchParams.get("prompt") || "Show the analytics flow."

  const dynamicSteps = React.useMemo(() => [
    { type: "reasoning", text: `Initializing sandbox for ${repo.split('/').pop()}...`, delay: 800 },
    { type: "action", text: "Security sandbox established. Isolation level: High.", delay: 1800 },
    { type: "reasoning", text: "Analyzing repository structure...", delay: 2800 },
    { type: "action", text: "Detected Next.js framework. Identifying routes...", delay: 3800 },
    { type: "reasoning", text: `Prompt analysis: "${prompt}"`, delay: 4800 },
    { type: "action", text: "Starting headless browser at http://localhost:3000/dashboard", delay: 5800 },
    { type: "reasoning", text: "Locating navigation elements...", delay: 7300 },
    { type: "action", text: "Interaction: Hovering over main navigation.", delay: 8800 },
    { type: "action", text: "Interaction: Clicking on target module.", delay: 10300 },
    { type: "milestone", text: "RECORDED: Primary workflow entry.", delay: 11800 },
    { type: "reasoning", text: "Capturing component state and interactions.", delay: 13300 },
    { type: "action", text: "Interaction: Performing requested demo steps.", delay: 14800 },
    { type: "milestone", text: "RECORDED: Feature interaction sequence.", delay: 16800 },
    { type: "reasoning", text: "Finalizing autonomous recording and stitching high-fidelity clips.", delay: 18800 },
  ], [repo, prompt])

  const [activeSteps, setActiveSteps] = React.useState<typeof dynamicSteps>([])
  const [progress, setProgress] = React.useState(0)
  const [isFinished, setIsFinished] = React.useState(false)
  const [currentBrowserAction, setCurrentBrowserAction] = React.useState("Idle")
  const [milestonesCount, setMilestonesCount] = React.useState(0)

  React.useEffect(() => {
    dynamicSteps.forEach((step, index) => {
      setTimeout(() => {
        setActiveSteps(prev => [...prev, step])
        setProgress(((index + 1) / dynamicSteps.length) * 100)
        
        if (step.type === "action") setCurrentBrowserAction(step.text)
        if (step.type === "milestone") setMilestonesCount(prev => prev + 1)
        
        if (index === dynamicSteps.length - 1) {
          setTimeout(() => setIsFinished(true), 2000)
        }
      }, step.delay)
    })
  }, [dynamicSteps])

  return (
    <div className="max-w-6xl mx-auto space-y-6 pb-12">
      {/* Header Info */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between bg-muted/30 p-4 rounded-xl border">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
            <Cpu className="h-6 w-6 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold truncate max-w-[200px]">{repo}</span>
              <Badge variant="outline" className="text-[10px] h-5">LIVE SESSION</Badge>
            </div>
            <p className="text-xs text-muted-foreground line-clamp-1 italic">"{prompt}"</p>
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
        {/* Agent Reasoning Log */}
        <Card className="lg:col-span-4 flex flex-col overflow-hidden bg-zinc-950 border-zinc-800">
          <div className="p-3 border-b border-zinc-800 bg-zinc-900/50 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Terminal className="h-4 w-4 text-zinc-400" />
              <span className="text-xs font-mono text-zinc-400">AG_ENGINE_LOGS</span>
            </div>
            <div className="flex gap-1">
              <div className="h-2 w-2 rounded-full bg-red-500/50" />
              <div className="h-2 w-2 rounded-full bg-yellow-500/50" />
              <div className="h-2 w-2 rounded-full bg-green-500/50" />
            </div>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-3 font-mono text-xs">
            <AnimatePresence initial={false}>
              {activeSteps.map((step, i) => (
                <motion.div 
                  key={i}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  className={`flex gap-2 ${
                    step.type === 'milestone' ? 'text-green-400' : 
                    step.type === 'action' ? 'text-zinc-300' : 'text-zinc-500'
                  }`}
                >
                  <span className="shrink-0">{`>`}</span>
                  <span className={step.type === 'milestone' ? 'font-bold' : ''}>{step.text}</span>
                </motion.div>
              ))}
            </AnimatePresence>
            <div className="h-4" />
          </div>
        </Card>

        {/* Browser Simulation */}
        <Card className="lg:col-span-8 flex flex-col overflow-hidden bg-background border shadow-2xl relative">
           <div className="h-10 border-b bg-muted/50 flex items-center px-4 gap-3">
             <div className="flex gap-1.5">
               <div className="h-3 w-3 rounded-full bg-border" />
               <div className="h-3 w-3 rounded-full bg-border" />
               <div className="h-3 w-3 rounded-full bg-border" />
             </div>
             <div className="flex-1 h-6 bg-background rounded border flex items-center px-2">
               <Search className="h-3 w-3 text-muted-foreground mr-2" />
               <span className="text-[10px] text-muted-foreground truncate">localhost:3000/dashboard/analytics</span>
             </div>
           </div>

           <div className="flex-1 relative bg-zinc-50 flex items-center justify-center overflow-hidden">
              {/* Mock App UI */}
              <div className="w-[90%] h-[80%] bg-white rounded-lg shadow-sm border border-zinc-200 p-6 space-y-4">
                <div className="flex items-center justify-between mb-8">
                  <div className="h-4 w-32 bg-zinc-100 rounded" />
                  <div className="flex gap-2">
                    <div className="h-8 w-8 rounded bg-zinc-100" />
                    <div className="h-8 w-8 rounded bg-zinc-100" />
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div className="h-24 bg-zinc-50 rounded-lg border border-zinc-100 p-3">
                    <div className="h-2 w-12 bg-zinc-100 rounded mb-2" />
                    <div className="h-4 w-8 bg-primary/20 rounded" />
                  </div>
                  <div className="h-24 bg-zinc-50 rounded-lg border border-zinc-100 p-3">
                    <div className="h-2 w-12 bg-zinc-100 rounded mb-2" />
                    <div className="h-4 w-8 bg-zinc-100 rounded" />
                  </div>
                  <div className="h-24 bg-zinc-50 rounded-lg border border-zinc-100 p-3">
                    <div className="h-2 w-12 bg-zinc-100 rounded mb-2" />
                    <div className="h-4 w-8 bg-zinc-100 rounded" />
                  </div>
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

              {/* AI Agent Cursor Simulation */}
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
                    AI AGENT: CLICK
                  </div>
                </div>
              </motion.div>

              {/* Recording Overlay */}
              <div className="absolute top-4 right-4 flex items-center gap-2 px-3 py-1.5 bg-red-500 text-white text-[10px] font-bold rounded-full animate-pulse shadow-lg z-30">
                <div className="h-2 w-2 rounded-full bg-white" />
                REC 1080P
              </div>

              {/* Finish Overlay */}
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
                      We've successfully autonomous-recorded 3 key milestones and generated a high-fidelity demo video.
                    </p>
                      <div className="flex gap-4">
                        <Button size="lg" className="rounded-full px-8" onClick={() => router.push('/dashboard')}>
                          Go to Dashboard
                        </Button>
                        <Button size="lg" variant="outline" className="rounded-full px-8" onClick={() => router.push('/dashboard/demo/1')}>
                          View Demo
                          <ArrowRight className="ml-2 h-4 w-4" />
                        </Button>
                      </div>
                  </motion.div>
                )}
              </AnimatePresence>
           </div>

           {/* Current Action Indicator */}
           <div className="h-12 border-t bg-muted/30 flex items-center px-4 justify-between">
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <Loader2 className="h-3 w-3 animate-spin" />
                <span>Status: <span className="text-foreground font-medium">{currentBrowserAction}</span></span>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="secondary" className="bg-primary/10 text-primary border-none text-[10px]">
                  {milestonesCount} Milestones
                </Badge>
              </div>
           </div>
        </Card>
      </div>
    </div>
  )
}
