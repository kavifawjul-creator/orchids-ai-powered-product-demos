"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import {
  User,
  Settings,
  Users,
  CreditCard,
  Bell,
  Shield,
  LogOut,
  Video,
  ChevronLeft,
} from "lucide-react";

const sidebarItems = [
  { name: "Profile", href: "/settings", icon: User },
  { name: "Team", href: "/settings/team", icon: Users },
  { name: "Billing", href: "/settings/billing", icon: CreditCard },
  { name: "Notifications", href: "/settings/notifications", icon: Bell },
  { name: "Security", href: "/settings/security", icon: Shield },
];

export default function SettingsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const supabase = createClient();
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    const getUser = async () => {
      const { data: { user } } = await supabase.auth.getUser();
      setUser(user);
    };
    getUser();
  }, [supabase]);

  const handleSignOut = async () => {
    await supabase.auth.signOut();
    window.location.href = "/";
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="border-b">
        <div className="container mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/dashboard" className="flex items-center gap-2 text-muted-foreground hover:text-foreground">
              <ChevronLeft className="h-4 w-4" />
              Back to Dashboard
            </Link>
          </div>
          <Link href="/" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center text-primary-foreground">
              <Video size={18} />
            </div>
            <span className="text-lg font-bold">AutoVidAI</span>
          </Link>
        </div>
      </div>

      <div className="container mx-auto px-6 py-8">
        <div className="flex gap-8">
          <aside className="w-64 shrink-0">
            <nav className="space-y-1">
              {sidebarItems.map((item) => {
                const isActive = pathname === item.href || 
                  (item.href !== "/settings" && pathname.startsWith(item.href));
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={cn(
                      "flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors",
                      isActive
                        ? "bg-primary text-primary-foreground"
                        : "text-muted-foreground hover:bg-muted hover:text-foreground"
                    )}
                  >
                    <item.icon className="h-4 w-4" />
                    {item.name}
                  </Link>
                );
              })}
            </nav>

            <div className="mt-8 pt-8 border-t">
              <Button
                variant="ghost"
                className="w-full justify-start text-red-600 hover:text-red-700 hover:bg-red-50"
                onClick={handleSignOut}
              >
                <LogOut className="h-4 w-4 mr-3" />
                Sign out
              </Button>
            </div>
          </aside>

          <main className="flex-1 max-w-3xl">{children}</main>
        </div>
      </div>
    </div>
  );
}
