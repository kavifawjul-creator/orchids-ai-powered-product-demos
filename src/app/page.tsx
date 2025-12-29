"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { 
  PlayCircle, 
  Code, 
  Monitor, 
  Cpu, 
  Zap, 
  RefreshCw, 
  Video, 
  MousePointer2,
  GitBranch,
  Terminal,
  Layers,
  Sparkles
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default function Home() {
  const fadeIn = {
    initial: { opacity: 0, y: 20 },
    animate: { 
      opacity: 1, 
      y: 0,
      transition: { duration: 0.6 }
    }
  };

  const staggerContainer = {
    animate: {
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  return (
    <div className="min-h-screen bg-background font-sans selection:bg-primary selection:text-primary-foreground">
      {/* Navigation */}
      <header className="fixed top-0 z-50 w-full border-b border-border/40 bg-background/80 backdrop-blur-md">
        <div className="container mx-auto flex h-16 items-center justify-between px-4 md:px-6">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
              <PlayCircle className="h-5 w-5" />
            </div>
            <span className="text-xl font-bold tracking-tighter">AutoVidAI</span>
          </div>
          <nav className="hidden gap-6 md:flex">
            <a href="#problem" className="text-sm font-medium text-muted-foreground transition-colors hover:text-primary">Problem</a>
            <a href="#solution" className="text-sm font-medium text-muted-foreground transition-colors hover:text-primary">Solution</a>
            <a href="#vision" className="text-sm font-medium text-muted-foreground transition-colors hover:text-primary">Vision</a>
          </nav>
          <Link href="/dashboard">
            <Button size="sm" className="rounded-full">Get Started</Button>
          </Link>
        </div>
      </header>

      <main>
        {/* Hero Section */}
        <section className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden pt-16">
          <div className="absolute inset-0 -z-10 bg-[radial-gradient(ellipse_at_center,var(--primary)/0.05,transparent_70%)]" />
          <div className="absolute inset-0 -z-10 bg-[linear-gradient(to_right,#8080800a_1px,transparent_1px),linear-gradient(to_bottom,#8080800a_1px,transparent_1px)] bg-[size:4rem_4rem]" />
          
          <motion.div 
            className="container px-4 text-center md:px-6"
            initial="initial"
            whileInView="animate"
            viewport={{ once: true }}
            variants={staggerContainer}
          >
            <motion.div variants={fadeIn}>
              <Badge variant="outline" className="mb-4 rounded-full border-primary/20 bg-primary/5 px-4 py-1 text-primary">
                Autonomous product videos, powered by AI
              </Badge>
            </motion.div>
            
            <motion.h1 
              className="mx-auto max-w-4xl text-5xl font-extrabold tracking-tight sm:text-7xl lg:text-8xl"
              variants={fadeIn}
            >
              Your software. <br />
              <span className="bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
                Demonstrating itself.
              </span>
            </motion.h1>
            
            <motion.p 
              className="mx-auto mt-6 max-w-2xl text-lg text-muted-foreground sm:text-xl"
              variants={fadeIn}
            >
              “Software should be able to explain itself.” <br />
              Turn your codebase into living demos automatically. No recording required.
            </motion.p>
            
            <motion.div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row" variants={fadeIn}>
              <Link href="/dashboard/new">
                <Button size="lg" className="h-14 rounded-full px-8 text-lg font-semibold shadow-xl shadow-primary/20">
                  Create Your First Demo
                </Button>
              </Link>
              <Button size="lg" variant="outline" className="h-14 rounded-full px-8 text-lg font-semibold">
                Watch it in Action
              </Button>
            </motion.div>

            {/* Visual Teaser */}
            <motion.div 
              className="mt-20 flex justify-center"
              variants={fadeIn}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.4, duration: 0.8 }}
            >
              <div className="relative h-[300px] w-full max-w-[800px] overflow-hidden rounded-2xl border border-border bg-card shadow-2xl md:h-[450px]">
                <div className="flex h-10 w-full items-center gap-2 border-b border-border bg-muted/50 px-4">
                  <div className="flex gap-1.5">
                    <div className="h-3 w-3 rounded-full bg-red-500/50" />
                    <div className="h-3 w-3 rounded-full bg-yellow-500/50" />
                    <div className="h-3 w-3 rounded-full bg-green-500/50" />
                  </div>
                  <div className="flex flex-1 justify-center">
                    <div className="h-5 w-1/2 rounded bg-muted-foreground/10" />
                  </div>
                </div>
                <div className="relative flex h-full flex-col items-center justify-center p-8 text-center">
                   <div className="flex items-center gap-4 mb-6">
                      <div className="p-3 bg-primary/10 rounded-full animate-pulse">
                        <Monitor className="h-8 w-8 text-primary" />
                      </div>
                      <div className="h-px w-12 bg-border" />
                      <div className="p-3 bg-primary/10 rounded-full">
                        <PlayCircle className="h-8 w-8 text-primary" />
                      </div>
                   </div>
                   <h3 className="text-xl font-semibold mb-2">Analyzing Repository...</h3>
                   <p className="text-muted-foreground max-w-sm">AI is navigating your dashboard, recording meaningful interactions, and generating video clips.</p>
                   
                   {/* Floating Elements for "AI Action" vibe */}
                   <motion.div 
                    className="absolute bottom-1/4 right-1/4 p-2 bg-background border rounded shadow-lg flex items-center gap-2"
                    animate={{ y: [0, -10, 0] }}
                    transition={{ repeat: Infinity, duration: 3 }}
                   >
                     <MousePointer2 className="h-4 w-4 text-primary" />
                     <span className="text-xs font-mono">click:#analytics-tab</span>
                   </motion.div>
                </div>
              </div>
            </motion.div>
          </motion.div>
        </section>

        {/* Problem Section */}
        <section id="problem" className="py-24 bg-muted/30">
          <div className="container mx-auto px-4 md:px-6">
            <div className="flex flex-col items-center text-center mb-16">
              <Badge variant="outline" className="mb-4">The Problem</Badge>
              <h2 className="text-3xl font-bold tracking-tight sm:text-4xl md:text-5xl">
                Product videos are slow, manual, and fragile.
              </h2>
              <p className="mt-4 max-w-2xl text-lg text-muted-foreground">
                Teams spend hours recording, only for the video to be outdated after the next UI change.
              </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {[
                { icon: Monitor, text: "Record screens manually" },
                { icon: RefreshCw, text: "Repeat flows again and again" },
                { icon: Video, text: "Re-record after every UI change" },
                { icon: Zap, text: "Struggle with complex software" }
              ].map((item, i) => (
                <motion.div key={i} variants={fadeIn}>
                  <Card className="border-border/50 bg-background/50 hover:border-primary/20 transition-all hover:shadow-lg h-full">
                    <CardContent className="pt-6">
                      <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center mb-4">
                        <item.icon className="h-5 w-5 text-primary" />
                      </div>
                      <p className="font-medium text-lg leading-snug">{item.text}</p>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </div>
            
            <div className="mt-16 text-center">
              <p className="text-xl font-medium italic text-muted-foreground">
                "The product already knows how it works — but video tools don’t understand products."
              </p>
            </div>
          </div>
        </section>

        {/* Insight Section */}
        <section className="py-24 overflow-hidden relative">
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-primary/5 rounded-full blur-[120px] -z-10" />
          <div className="container mx-auto px-4 md:px-6 text-center">
            <Badge className="mb-4 bg-primary/10 text-primary border-none">The Insight</Badge>
            <h2 className="text-4xl md:text-6xl font-bold tracking-tighter mb-8 leading-tight">
              What if software could <br />
              <span className="text-primary italic">demonstrate itself?</span>
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mt-16 max-w-5xl mx-auto">
              {[
                { icon: Code, title: "Read your code", desc: "Understand your product from the source." },
                { icon: Cpu, title: "Run your app", desc: "Operate in a real browser session." },
                { icon: MousePointer2, title: "Interact like a user", desc: "Autonomous navigation through features." },
                { icon: Layers, title: "Identify value", desc: "Understand which features matter most." }
              ].map((feature, i) => (
                <motion.div 
                  key={i} 
                  className="flex flex-col items-center"
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.1 }}
                >
                  <div className="h-12 w-12 rounded-xl bg-primary flex items-center justify-center text-primary-foreground mb-4 shadow-lg shadow-primary/20">
                    <feature.icon className="h-6 w-6" />
                  </div>
                  <h3 className="font-bold mb-2">{feature.title}</h3>
                  <p className="text-sm text-muted-foreground">{feature.desc}</p>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* Solution Section */}
        <section id="solution" className="py-24 bg-zinc-950 text-zinc-50">
          <div className="container mx-auto px-4 md:px-6">
            <div className="flex flex-col md:flex-row gap-12 items-center">
              <div className="flex-1 space-y-8">
                <motion.div variants={fadeIn} initial="initial" whileInView="animate" viewport={{ once: true }}>
                  <Badge variant="outline" className="border-zinc-800 text-zinc-400 mb-4">The Solution</Badge>
                  <h2 className="text-4xl md:text-5xl font-bold tracking-tight mb-6">
                    From codebase to living demo in minutes.
                  </h2>
                  <p className="text-xl text-zinc-400">
                    Your platform turns a codebase into a professional demo. No scripts, no screen recording, no rework.
                  </p>
                </motion.div>
                
                <div className="space-y-6">
                  {[
                    { step: "1", title: "Provide a Repository", desc: "Link your GitHub repo or upload your application files." },
                    { step: "2", title: "Simple Prompt", desc: "\"Create a product demo of our analytics dashboard.\"" },
                    { step: "3", title: "Autonomous Execution", desc: "The AI understands, navigates, and records the app live." },
                    { step: "4", title: "Final Video", desc: "Editable clips ready for export, narration, and captions." }
                  ].map((step, i) => (
                    <motion.div 
                      key={i} 
                      className="flex gap-4"
                      initial={{ opacity: 0, x: -20 }}
                      whileInView={{ opacity: 1, x: 0 }}
                      viewport={{ once: true }}
                      transition={{ delay: i * 0.1 }}
                    >
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-zinc-800 text-sm font-bold">
                        {step.step}
                      </div>
                      <div>
                        <h4 className="font-bold text-lg">{step.title}</h4>
                        <p className="text-zinc-500">{step.desc}</p>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>
              
              <motion.div 
                className="flex-1 w-full max-w-[500px]"
                initial={{ opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
              >
                <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-6 shadow-2xl">
                  <div className="space-y-4">
                    <div className="flex items-center gap-3 p-3 bg-zinc-800/50 rounded-lg border border-zinc-700">
                      <GitBranch className="h-5 w-5 text-zinc-500" />
                      <span className="text-sm font-mono text-zinc-300">github.com/acme/app</span>
                    </div>
                    <div className="p-4 bg-zinc-950 rounded-lg border border-zinc-800">
                      <p className="text-xs font-mono text-zinc-500 mb-2">PROMPT</p>
                      <p className="text-sm">Create a walkthrough of the new onboarding flow and the billing dashboard.</p>
                    </div>
                    <div className="space-y-2">
                      <div className="flex justify-between text-xs font-mono text-zinc-500">
                        <span>AI REASONING</span>
                        <span className="animate-pulse">RUNNING</span>
                      </div>
                      <div className="h-1.5 w-full bg-zinc-800 rounded-full overflow-hidden">
                        <motion.div 
                          className="h-full bg-primary"
                          initial={{ width: 0 }}
                          whileInView={{ width: "70%" }}
                          transition={{ duration: 2, repeat: Infinity }}
                        />
                      </div>
                      <div className="p-3 bg-zinc-800/30 rounded border border-zinc-800/50 font-mono text-[10px] text-zinc-400">
                        {`> Found route: /onboarding`} <br />
                        {`> Interacting with UserForm component...`} <br />
                        {`> Feature milestone: Onboarding Start`}
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>
            </div>
          </div>
        </section>

        {/* Differentiation Section */}
        <section className="py-24">
          <div className="container mx-auto px-4 md:px-6">
            <div className="flex flex-col items-center text-center mb-16">
              <Badge variant="outline" className="mb-4">What Makes It Different</Badge>
              <h2 className="text-3xl font-bold tracking-tight sm:text-4xl md:text-5xl">
                This is not a video generator.
              </h2>
              <p className="mt-4 max-w-2xl text-lg text-muted-foreground">
                It's an autonomous product agent that understands your software at its core.
              </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto">
              <motion.div 
                className="p-8 rounded-2xl border bg-background space-y-4 shadow-sm"
                whileHover={{ y: -5 }}
                transition={{ type: "spring", stiffness: 300 }}
              >
                <div className="h-12 w-12 rounded-xl bg-primary/10 flex items-center justify-center text-primary mb-2">
                  <Cpu className="h-6 w-6" />
                </div>
                <h3 className="text-xl font-bold">Autonomous Agent</h3>
                <ul className="space-y-3">
                  {[
                    "Autonomous product agent",
                    "Browser-native system",
                    "Feature-aware recorder",
                    "Structured video editor"
                  ].map((text, i) => (
                    <li key={i} className="flex items-center gap-2 text-muted-foreground">
                      <div className="h-1.5 w-1.5 rounded-full bg-primary" />
                      {text}
                    </li>
                  ))}
                </ul>
              </motion.div>
              <motion.div 
                className="p-8 rounded-2xl border bg-background space-y-4 shadow-sm"
                whileHover={{ y: -5 }}
                transition={{ type: "spring", stiffness: 300 }}
              >
                <div className="h-12 w-12 rounded-xl bg-primary/10 flex items-center justify-center text-primary mb-2">
                  <Sparkles className="h-6 w-6" />
                </div>
                <h3 className="text-xl font-bold">Reproducible Result</h3>
                <ul className="space-y-3">
                  {[
                    "Intentional clips",
                    "Explainable actions",
                    "Reproducible flows",
                    "Instantly updatable"
                  ].map((text, i) => (
                    <li key={i} className="flex items-center gap-2 text-muted-foreground">
                      <div className="h-1.5 w-1.5 rounded-full bg-primary" />
                      {text}
                    </li>
                  ))}
                </ul>
              </motion.div>
            </div>
          </div>
        </section>

        {/* Vision Statement / CTA */}
        <section id="vision" className="py-32 relative overflow-hidden bg-primary text-primary-foreground">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(255,255,255,0.1),transparent)]" />
          <div className="container mx-auto px-4 md:px-6 relative text-center">
            <motion.h2 
              className="text-4xl md:text-6xl font-extrabold tracking-tighter mb-8 italic"
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
            >
              “Software should be able to explain itself.”
            </motion.h2>
            <motion.p 
              className="max-w-2xl mx-auto text-xl opacity-90 mb-12"
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.1 }}
            >
              AutoVidAI becomes the demo engineer, the onboarding guide, and the product marketer for your team. All powered by the product itself.
            </motion.p>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.2 }}
            >
              <Link href="/dashboard/new">
                <Button size="lg" variant="secondary" className="h-16 rounded-full px-10 text-xl font-bold shadow-2xl hover:scale-105 transition-transform">
                  Start Building with AutoVidAI
                </Button>
              </Link>
            </motion.div>
            
            <div className="mt-16 flex flex-wrap justify-center gap-8 opacity-60">
              <div className="flex items-center gap-2">
                <Terminal className="h-5 w-5" />
                <span className="text-sm font-medium">Demo Engineer</span>
              </div>
              <div className="flex items-center gap-2">
                <Monitor className="h-5 w-5" />
                <span className="text-sm font-medium">Onboarding Guide</span>
              </div>
              <div className="flex items-center gap-2">
                <Sparkles className="h-5 w-5" />
                <span className="text-sm font-medium">Product Marketer</span>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t py-12 bg-muted/20">
        <div className="container mx-auto px-4 md:px-6">
          <div className="flex flex-col md:flex-row justify-between items-center gap-8">
            <div className="flex items-center gap-2">
              <PlayCircle className="h-6 w-6 text-primary" />
              <span className="text-xl font-bold tracking-tighter">AutoVidAI</span>
            </div>
            <div className="flex gap-8 text-sm text-muted-foreground">
              <a href="#" className="hover:text-primary transition-colors">Privacy</a>
              <a href="#" className="hover:text-primary transition-colors">Terms</a>
              <a href="#" className="hover:text-primary transition-colors">Twitter</a>
              <a href="#" className="hover:text-primary transition-colors">GitHub</a>
            </div>
            <p className="text-sm text-muted-foreground">
              © 2024 AutoVidAI. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
