"use client";

import { useEffect, useState } from "react";
import { KPICard } from "./kpi-card";
import { Activity, AlertTriangle, FileText, ShieldCheck, Clock, PieChart as PieChartIcon, BarChart3 } from "lucide-react";
import Link from "next/link";
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid } from "recharts";

export function UnifiedDashboard() {
  const [data, setData] = useState({
    kpis: {
      total_tickets: 0,
      open_tickets: 0,
      total_actions: 0
    },
    recent_reports: [],
    charts: {
      reports_by_status: [],
      reports_by_department: []
    }
  });

  const [performanceData, setPerformanceData] = useState<any>(null);

  const fetchData = () => {
    fetch("http://127.0.0.1:8000/api/v1/dashboards/unified")
      .then(res => res.json())
      .then(data => setData(data))
      .catch(err => console.error("Failed to fetch dashboard data:", err));

    fetch("http://127.0.0.1:8000/api/v1/dashboards/analytics/performance")
      .then(res => res.json())
      .then(data => setPerformanceData(data))
      .catch(err => console.error("Failed to fetch performance data:", err));
  };

  useEffect(() => {
    fetchData();

    // Setup SSE connection for real-time updates
    const eventSource = new EventSource("http://127.0.0.1:8000/api/v1/stream/events");
    
    eventSource.onmessage = (event) => {
      fetchData();
    };

    return () => eventSource.close();
  }, []);

  return (
    <div className="space-y-8">
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <KPICard 
          title="Total Tickets" 
          value={data.kpis.total_tickets} 
          icon={<FileText />}
          description="Global event volume"
          trend="+12%"
        />
        <KPICard 
          title="Open Incidents" 
          value={data.kpis.open_tickets} 
          icon={<AlertTriangle className="text-sentinel-amber" />}
          description="Requiring immediate review"
          trend="Active"
        />
        <KPICard 
          title="Agent Actions" 
          value={data.kpis.total_actions} 
          icon={<Activity className="text-sentinel-blue" />}
          description="Executed recommendations"
          trend="Live"
        />
        <KPICard 
          title="Security Status" 
          value="Secured" 
          icon={<ShieldCheck className="text-sentinel-green" />}
          description="Zero-trust layer active"
        />
      </div>

      <div className="grid gap-8 lg:grid-cols-2">
        <div className="glass-card rounded-xl p-6 border border-border/50">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-bold flex items-center gap-2">
              <Clock className="h-5 w-5 text-primary" />
              Latest Agent Intelligence
            </h3>
            <Link href="/tickets" className="text-sm font-medium text-primary hover:underline">View all tickets</Link>
          </div>
          
          <div className="space-y-4">
            {data.recent_reports && data.recent_reports.length > 0 ? (
              data.recent_reports.map((report: any) => (
                <div key={report.id} className="p-4 border border-border/30 rounded-lg bg-secondary/20 hover:bg-secondary/40 transition-colors">
                  <div className="flex justify-between items-center mb-3">
                    <span className="font-bold text-sentinel-blue text-sm">{report.department_id}</span>
                    <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase tracking-widest ${
                      report.status === 'pending' ? 'badge-pending' : 
                      report.status === 'validated' ? 'badge-validated' : 
                      'badge-modified'
                    }`}>
                      {report.status}
                    </span>
                  </div>
                  <p className="text-xs text-foreground line-clamp-2 mb-2 leading-relaxed italic">
                    "{report.content?.analysis}"
                  </p>
                  <div className="flex justify-between items-center mt-3 pt-3 border-t border-border/20">
                    <span className="text-[10px] text-muted-foreground font-mono">TKT #{report.ticket_id}</span>
                    <span className="text-[10px] font-bold text-muted-foreground uppercase">Confidence: {report.content?.confidence}</span>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-12 text-muted-foreground border border-dashed border-border rounded-lg">
                <p>Waiting for intelligence reports...</p>
              </div>
            )}
          </div>
        </div>

        <div className="flex flex-col gap-6">
          {/* Charts Section */}
          <div className="grid gap-6 md:grid-cols-2">
            <div className="glass-card rounded-xl p-4 border border-border/50">
              <h3 className="text-sm font-bold flex items-center gap-2 mb-4">
                <PieChartIcon className="h-4 w-4" /> Reports by Status
              </h3>
              <div className="h-[200px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={data.charts?.reports_by_status || []}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={80}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {(data.charts?.reports_by_status || []).map((entry: any, index: number) => (
                        <Cell key={`cell-${index}`} fill={
                          entry.name === 'pending' ? '#f59e0b' : 
                          entry.name === 'validated' ? '#10b981' : 
                          entry.name === 'invalidated' ? '#ef4444' : '#3b82f6'
                        } />
                      ))}
                    </Pie>
                    <Tooltip 
                      contentStyle={{ backgroundColor: 'hsl(var(--background))', borderColor: 'hsl(var(--border))' }}
                      itemStyle={{ color: 'hsl(var(--foreground))' }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="glass-card rounded-xl p-4 border border-border/50">
              <h3 className="text-sm font-bold flex items-center gap-2 mb-4">
                <BarChart3 className="h-4 w-4" /> Activity by Dept
              </h3>
              <div className="h-[200px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data.charts?.reports_by_department || []} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                    <XAxis dataKey="name" tick={{ fontSize: 10 }} tickLine={false} axisLine={false} />
                    <YAxis tick={{ fontSize: 10 }} tickLine={false} axisLine={false} />
                    <Tooltip 
                      contentStyle={{ backgroundColor: 'hsl(var(--background))', borderColor: 'hsl(var(--border))' }}
                      cursor={{ fill: 'hsl(var(--secondary))' }}
                    />
                    <Bar dataKey="value" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          <div className="glass-card rounded-xl p-6 border border-border/50 bg-gradient-to-br from-primary/10 via-transparent to-transparent">
            <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
              <Activity className="h-5 w-5 text-primary" />
              Agent Performance Analytics
            </h3>
            
            {performanceData ? (
              <>
                <div className="grid grid-cols-2 gap-4 mb-6">
                  <div className="bg-background/50 p-4 rounded-lg border border-border/50">
                    <div className="text-xs text-muted-foreground uppercase font-bold mb-1">Agents Active</div>
                    <div className="text-xl font-bold">{performanceData.active_agents} / 6</div>
                  </div>
                  <div className="bg-background/50 p-4 rounded-lg border border-border/50">
                    <div className="text-xs text-muted-foreground uppercase font-bold mb-1">System Health</div>
                    <div className="text-xl font-bold text-sentinel-green capitalize">{performanceData.overall_system_health}</div>
                  </div>
                </div>

                <div className="h-[200px] w-full mt-4">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={performanceData.performance} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                      <XAxis dataKey="department_id" tick={{ fontSize: 9 }} tickLine={false} axisLine={false} />
                      <YAxis yAxisId="left" tick={{ fontSize: 10 }} tickLine={false} axisLine={false} />
                      <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 10 }} tickLine={false} axisLine={false} domain={[0, 1]} />
                      <Tooltip 
                        contentStyle={{ backgroundColor: 'hsl(var(--background))', borderColor: 'hsl(var(--border))' }}
                        cursor={{ fill: 'hsl(var(--secondary))' }}
                      />
                      <Legend wrapperStyle={{ fontSize: '10px' }} />
                      <Bar yAxisId="left" dataKey="reports_processed" name="Throughput" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
                      <Bar yAxisId="right" dataKey="avg_confidence_score" name="Avg Confidence" fill="hsl(var(--sentinel-amber))" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </>
            ) : (
              <p className="text-muted-foreground text-sm">Loading analytics...</p>
            )}
          </div>
          
          <div className="glass-card rounded-xl p-6 border border-border/50 flex items-center justify-between group cursor-pointer hover:border-primary/50 transition-colors">
            <div>
              <h4 className="font-bold text-lg">Governance Audit Trail</h4>
              <p className="text-xs text-muted-foreground">Check cryptographically signed decision logs.</p>
            </div>
            <Link href="/audit" className="p-3 bg-secondary rounded-full group-hover:bg-primary group-hover:text-primary-foreground transition-all">
              <Activity className="h-5 w-5" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
