"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { motion, useScroll, useTransform } from "framer-motion";
import { 
  Play, 
  ArrowRight, 
  Zap, 
  Bot, 
  Code2, 
  Sparkles, 
  CheckCircle2, 
  Layers, 
  ShieldCheck,
  Video,
  Monitor,
  Cpu,
  MousePointer2,
  Menu,
  X
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

const Nav = () => {
  const [isScrolled, setIsScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 20);
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
      isScrolled ? "bg-background/80 backdrop-blur-md border-b py-3" : "bg-transparent py-6"
    }`}>
      <div className="container mx-auto px-6 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 group">
          <div className="w-10 h-10 rounded-xl bg-primary flex items-center justify-center text-primary-foreground shadow-lg shadow-primary/20 group-hover:scale-110 transition-transform">
            <Video size={22} className="fill-current" />
          </div>
          <span className="text-xl font-bold tracking-tight">AutoVidAI</span>
        </Link>

        <div className="hidden md:flex items-center gap-8">
          {["Features", "Solutions", "How it Works", "Pricing"].map((item) => (
            <Link 
              key={item} 
              href={`#${item.toLowerCase().replace(/\s+/g, "-")}`} 
              className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors"
            >
              {item}
            </Link>
          ))}
        </div>

        <div className="hidden md:flex items-center gap-4">
          <Link href="/dashboard">
            <Button variant="ghost" size="sm">Sign In</Button>
          </Link>
          <Link href="/dashboard">
            <Button size="sm" className="rounded-full px-6 shadow-lg shadow-primary/20">
              Get Started
            </Button>
          </Link>
        </div>

        <button 
          className="md:hidden text-foreground"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
        >
          {mobileMenuOpen ? <X /> : <Menu />}
        </button>
      </div>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="md:hidden absolute top-full left-0 right-0 bg-background border-b p-6 flex flex-col gap-4 shadow-xl"
        >
          {["Features", "Solutions", "How it Works", "Pricing"].map((item) => (
            <Link 
              key={item} 
              href="#" 
              onClick={() => setMobileMenuOpen(false)}
              className="text-lg font-medium py-2"
            >
              {item}
            </Link>
          ))}
          <hr className="my-2" />
          <div className="flex flex-col gap-3">
            <Button variant="outline" fullWidth>Sign In</Button>
            <Button fullWidth>Get Started</Button>
          </div>
        </motion.div>
      )}
    </nav>
  );
};

const Hero = () => {
  return (
    <section className="relative pt-32 pb-20 overflow-hidden">
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-6xl h-full opacity-30 pointer-events-none">
        <div className="absolute top-20 left-10 w-72 h-72 bg-primary/20 rounded-full blur-[120px]" />
        <div className="absolute bottom-20 right-10 w-96 h-96 bg-blue-500/10 rounded-full blur-[150px]" />
      </div>

      <div className="container mx-auto px-6 relative z-10 text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <Badge variant="secondary" className="mb-6 px-4 py-1.5 rounded-full bg-primary/10 text-primary border-primary/20 gap-2">
            <Sparkles size={14} className="fill-current" />
            Autonomous Product Demos is Here
          </Badge>
          <h1 className="text-5xl md:text-7xl font-bold tracking-tight mb-6 max-w-4xl mx-auto leading-[1.1]">
            Turn your code into <span className="text-primary italic">interactive</span> video demos instantly.
          </h1>
          <p className="text-xl text-muted-foreground mb-10 max-w-2xl mx-auto">
            AutoVidAI's autonomous agents explore your application, record workflows, and generate professional video walkthroughs directly from your repository.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link href="/dashboard">
              <Button size="xl" className="rounded-full px-8 h-14 text-lg shadow-xl shadow-primary/20 gap-2 group">
                Build your first demo <ArrowRight className="group-hover:translate-x-1 transition-transform" />
              </Button>
            </Link>
            <Button variant="outline" size="xl" className="rounded-full px-8 h-14 text-lg gap-2">
              <Play size={18} fill="currentColor" /> Watch 60s Video
            </Button>
          </div>

          <div className="mt-16 relative mx-auto max-w-5xl group">
            <div className="absolute -inset-1 bg-gradient-to-r from-primary to-blue-600 rounded-2xl blur opacity-25 group-hover:opacity-40 transition duration-1000"></div>
            <div className="relative aspect-video rounded-2xl bg-card border shadow-2xl overflow-hidden flex items-center justify-center">
              <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1550751827-4bd374c3f58b?auto=format&fit=crop&q=80&w=1200')] bg-cover bg-center opacity-40"></div>
              <div className="absolute inset-0 bg-gradient-to-t from-background to-transparent opacity-80"></div>
              
              <div className="relative z-10 flex flex-col items-center gap-6">
                <div className="w-20 h-20 rounded-full bg-primary flex items-center justify-center text-primary-foreground shadow-2xl shadow-primary/40 group-hover:scale-110 transition-transform cursor-pointer">
                  <Play size={32} fill="currentColor" className="ml-1" />
                </div>
                <div className="flex items-center gap-4">
                   <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-black/50 backdrop-blur-md border border-white/10 text-xs font-mono text-white">
                     <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                     LIVE AGENT RECORDING
                   </div>
                   <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-black/50 backdrop-blur-md border border-white/10 text-xs font-mono text-white">
                     <Code2 size={12} />
                     repo: acme-dashboard
                   </div>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
};

const Features = () => {
  const features = [
    {
      title: "Autonomous Exploration",
      description: "Our AI agents crawl your application's routes and components to find the most valuable user journeys.",
      icon: Bot,
      color: "bg-blue-500"
    },
    {
      title: "Zero Setup Video",
      description: "No screen recording required. The agent captures high-fidelity interactions directly in a headless browser.",
      icon: Video,
      color: "bg-primary"
    },
    {
      title: "AI Voice Narration",
      description: "Generate professional voiceovers in multiple languages and tones that match your brand perfectly.",
      icon: Cpu,
      color: "bg-purple-500"
    },
    {
      title: "Brand Consistency",
      description: "Automatically apply your brand colors, fonts, and logo to every generated demo video.",
      icon: Sparkles,
      color: "bg-orange-500"
    },
    {
      title: "Smart Annotations",
      description: "AI-generated tooltips and callouts highlight key features and benefits during the walkthrough.",
      icon: MousePointer2,
      color: "bg-emerald-500"
    },
    {
      title: "One-Click Updates",
      description: "Redeploying code? AutoVidAI detects changes and regenerates your demos automatically.",
      icon: Zap,
      color: "bg-red-500"
    }
  ];

  return (
    <section id="features" className="py-24 bg-muted/30">
      <div className="container mx-auto px-6">
        <div className="text-center mb-16">
          <Badge className="mb-4">Capabilities</Badge>
          <h2 className="text-4xl font-bold mb-4">Everything you need to showcase your product</h2>
          <p className="text-muted-foreground max-w-2xl mx-auto text-lg">
            Stop wasting hours recording and editing videos. AutoVidAI automates the entire product marketing pipeline.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.1 }}
              viewport={{ once: true }}
              className="p-8 rounded-2xl bg-card border hover:border-primary/40 transition-colors shadow-sm group"
            >
              <div className={`w-12 h-12 rounded-xl ${feature.color} flex items-center justify-center text-white mb-6 group-hover:scale-110 transition-transform`}>
                <feature.icon size={24} />
              </div>
              <h3 className="text-xl font-bold mb-3">{feature.title}</h3>
              <p className="text-muted-foreground leading-relaxed">
                {feature.description}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

const HowItWorks = () => {
  const steps = [
    {
      title: "Connect Repo",
      description: "Paste your GitHub URL and our AI analyzes your codebase structure and UI.",
      icon: Code2
    },
    {
      title: "Define Scenarios",
      description: "Tell the agent what to showcase, or let it discover key workflows automatically.",
      icon: Layers
    },
    {
      title: "Agent Execution",
      description: "The agent navigates your live app, recording interactions and logging insights.",
      icon: Monitor
    },
    {
      title: "Share Everywhere",
      description: "Export as high-quality video or embed as interactive demos on your site.",
      icon: CheckCircle2
    }
  ];

  return (
    <section id="how-it-works" className="py-24">
      <div className="container mx-auto px-6">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold mb-4">From repo to demo in minutes</h2>
        </div>

        <div className="grid md:grid-cols-4 gap-12 relative">
          <div className="hidden md:block absolute top-12 left-[15%] right-[15%] h-0.5 bg-border z-0" />
          
          {steps.map((step, idx) => (
            <div key={idx} className="relative z-10 flex flex-col items-center text-center">
              <div className="w-16 h-16 rounded-full bg-background border-4 border-primary/20 flex items-center justify-center text-primary mb-6 shadow-xl">
                <step.icon size={28} />
              </div>
              <h3 className="text-xl font-bold mb-2">{step.title}</h3>
              <p className="text-muted-foreground">{step.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

const Footer = () => {
  return (
    <footer className="bg-background border-t py-12">
      <div className="container mx-auto px-6">
        <div className="flex flex-col md:flex-row justify-between items-center gap-8">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center text-primary-foreground">
              <Video size={18} />
            </div>
            <span className="text-lg font-bold">AutoVidAI</span>
          </div>
          
          <div className="flex gap-8 text-sm text-muted-foreground">
            <Link href="#" className="hover:text-primary">Privacy</Link>
            <Link href="#" className="hover:text-primary">Terms</Link>
            <Link href="#" className="hover:text-primary">Twitter</Link>
            <Link href="#" className="hover:text-primary">Support</Link>
          </div>
          
          <p className="text-sm text-muted-foreground">
            © 2024 AutoVidAI. Built for developers.
          </p>
        </div>
      </div>
    </footer>
  );
};

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-background">
      <Nav />
      <Hero />
      <Features />
      <HowItWorks />
      
      {/* CTA Section */}
      <section className="py-24">
        <div className="container mx-auto px-6">
          <div className="bg-primary rounded-[2.5rem] p-12 md:p-20 text-center relative overflow-hidden shadow-2xl shadow-primary/20">
            <div className="absolute top-0 left-0 w-full h-full bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] opacity-10" />
            <div className="relative z-10">
              <h2 className="text-4xl md:text-5xl font-bold text-primary-foreground mb-6">
                Ready to automate your product marketing?
              </h2>
              <p className="text-primary-foreground/80 text-xl mb-10 max-w-2xl mx-auto">
                Join 500+ engineering teams saving 20+ hours a month on video production.
              </p>
              <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                <Link href="/dashboard">
                  <Button size="xl" variant="secondary" className="rounded-full px-10 h-14 text-lg font-bold shadow-xl">
                    Get Started for Free
                  </Button>
                </Link>
                <Button variant="outline" size="xl" className="rounded-full px-10 h-14 text-lg bg-transparent border-primary-foreground/20 text-primary-foreground hover:bg-primary-foreground/10">
                  Contact Sales
                </Button>
              </div>
            </div>
          </div>
        </div>
      </section>

      <Footer />
    </main>
  );
}
