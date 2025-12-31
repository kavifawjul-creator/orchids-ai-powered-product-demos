"use client";

import { useState, useEffect } from "react";
import { createClient } from "@/lib/supabase/client";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, TrendingUp, Eye, Play, Users, Video, Clock, Share2 } from "lucide-react";

interface AnalyticsData {
  totalDemos: number;
  totalViews: number;
  totalShares: number;
  publicDemos: number;
  recentViews: { date: string; count: number }[];
  topDemos: { id: string; title: string; views: number }[];
}

export default function AnalyticsDashboardPage() {
  const supabase = createClient();
  const [loading, setLoading] = useState(true);
  const [analytics, setAnalytics] = useState<AnalyticsData>({
    totalDemos: 0,
    totalViews: 0,
    totalShares: 0,
    publicDemos: 0,
    recentViews: [],
    topDemos: [],
  });

  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) return;

    const { data: workspace } = await supabase
      .from("workspaces")
      .select("id")
      .eq("owner_id", user.id)
      .single();

    if (!workspace) {
      setLoading(false);
      return;
    }

    const { data: demos } = await supabase
      .from("demos")
      .select("id, title, is_public")
      .eq("workspace_id", workspace.id);

    const demoIds = demos?.map((d) => d.id) || [];

    const { data: analyticsData } = await supabase
      .from("analytics")
      .select("*")
      .in("demo_id", demoIds);

    const views = analyticsData?.filter((a) => a.event_type === "view") || [];
    const shares = analyticsData?.filter((a) => a.event_type === "share") || [];

    const last7Days: { date: string; count: number }[] = [];
    for (let i = 6; i >= 0; i--) {
      const date = new Date();
      date.setDate(date.getDate() - i);
      const dateStr = date.toISOString().split("T")[0];
      const count = views.filter(
        (v) => v.created_at?.split("T")[0] === dateStr
      ).length;
      last7Days.push({ date: dateStr, count });
    }

    const viewsPerDemo: Record<string, number> = {};
    views.forEach((v) => {
      viewsPerDemo[v.demo_id] = (viewsPerDemo[v.demo_id] || 0) + 1;
    });

    const topDemos = demos
      ?.map((d) => ({
        id: d.id,
        title: d.title,
        views: viewsPerDemo[d.id] || 0,
      }))
      .sort((a, b) => b.views - a.views)
      .slice(0, 5) || [];

    setAnalytics({
      totalDemos: demos?.length || 0,
      totalViews: views.length,
      totalShares: shares.length,
      publicDemos: demos?.filter((d) => d.is_public).length || 0,
      recentViews: last7Days,
      topDemos,
    });

    setLoading(false);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const statCards = [
    {
      title: "Total Demos",
      value: analytics.totalDemos,
      icon: Video,
      description: "Created demos",
      color: "text-blue-600 bg-blue-100",
    },
    {
      title: "Total Views",
      value: analytics.totalViews,
      icon: Eye,
      description: "Across all demos",
      color: "text-green-600 bg-green-100",
    },
    {
      title: "Total Shares",
      value: analytics.totalShares,
      icon: Share2,
      description: "Demo shares",
      color: "text-purple-600 bg-purple-100",
    },
    {
      title: "Public Demos",
      value: analytics.publicDemos,
      icon: Users,
      description: "Publicly accessible",
      color: "text-orange-600 bg-orange-100",
    },
  ];

  const maxViews = Math.max(...analytics.recentViews.map((d) => d.count), 1);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Analytics</h1>
        <p className="text-muted-foreground">
          Track the performance of your demos
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {statCards.map((stat) => (
          <Card key={stat.title}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{stat.title}</CardTitle>
              <div className={`p-2 rounded-lg ${stat.color}`}>
                <stat.icon className="h-4 w-4" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
              <p className="text-xs text-muted-foreground">{stat.description}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Views Over Time</CardTitle>
            <CardDescription>Last 7 days</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {analytics.recentViews.map((day) => (
                <div key={day.date} className="flex items-center gap-3">
                  <span className="text-sm text-muted-foreground w-20">
                    {new Date(day.date).toLocaleDateString("en-US", {
                      weekday: "short",
                      month: "short",
                      day: "numeric",
                    })}
                  </span>
                  <div className="flex-1 h-6 bg-muted rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary rounded-full transition-all"
                      style={{ width: `${(day.count / maxViews) * 100}%` }}
                    />
                  </div>
                  <span className="text-sm font-medium w-8 text-right">
                    {day.count}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Top Performing Demos</CardTitle>
            <CardDescription>By view count</CardDescription>
          </CardHeader>
          <CardContent>
            {analytics.topDemos.length > 0 ? (
              <div className="space-y-4">
                {analytics.topDemos.map((demo, index) => (
                  <div key={demo.id} className="flex items-center gap-3">
                    <span className="flex items-center justify-center w-6 h-6 rounded-full bg-muted text-xs font-medium">
                      {index + 1}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{demo.title}</p>
                    </div>
                    <div className="flex items-center gap-1 text-muted-foreground">
                      <Eye className="h-3 w-3" />
                      <span className="text-sm">{demo.views}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <Video className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p>No demos yet</p>
                <p className="text-sm">Create your first demo to see analytics</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Quick Stats</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            <div className="flex items-center gap-4 p-4 rounded-lg bg-muted/50">
              <div className="p-3 rounded-full bg-blue-100">
                <TrendingUp className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Avg. Views per Demo</p>
                <p className="text-xl font-bold">
                  {analytics.totalDemos > 0
                    ? Math.round(analytics.totalViews / analytics.totalDemos)
                    : 0}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-4 p-4 rounded-lg bg-muted/50">
              <div className="p-3 rounded-full bg-green-100">
                <Clock className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Views Today</p>
                <p className="text-xl font-bold">
                  {analytics.recentViews[analytics.recentViews.length - 1]?.count || 0}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-4 p-4 rounded-lg bg-muted/50">
              <div className="p-3 rounded-full bg-purple-100">
                <Play className="h-5 w-5 text-purple-600" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Public Rate</p>
                <p className="text-xl font-bold">
                  {analytics.totalDemos > 0
                    ? Math.round((analytics.publicDemos / analytics.totalDemos) * 100)
                    : 0}
                  %
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
