"use client";

import { useEffect, useState } from "react";
import { useSSE } from "@/lib/hooks";
import { ReportCard } from "./report-card";
import { fetchReports } from "@/lib/api";
import { CheckCircle2, ShieldCheck, Route, Network, AlertCircle } from "lucide-react";

export function LivePipeline({ ticketId, initialPayload }: { ticketId: string, initialPayload: any }) {
  const { events, isConnected } = useSSE("http://127.0.0.1:8000/api/v1/stream/events");
  const [reports, setReports] = useState<any[]>([]);
  const [pipelineState, setPipelineState] = useState({
    inputReceived: true,
    securityChecked: true, // Mocked as fast
    routingComplete: false,
    targetDepts: [] as string[],
    analysisComplete: false,
  });

  // Fetch existing reports on mount
  useEffect(() => {
    fetchReports(ticketId).then(data => {
      setReports(data);
      if (data.length > 0) {
        setPipelineState(prev => ({ ...prev, routingComplete: true, targetDepts: data.map((r: any) => r.department_id) }));
      }
    });
  }, [ticketId]);

  // Process SSE events
  useEffect(() => {
    const relevantEvents = events.filter(e => e.data?.ticket_id === parseInt(ticketId));
    
    for (const event of relevantEvents) {
      if (event.type === "routing_complete") {
        setPipelineState(prev => ({ 
          ...prev, 
          routingComplete: true, 
          targetDepts: event.data.target_depts 
        }));
      }
      
      if (event.type === "agent_started") {
        // Add a placeholder if not exists
        setReports(prev => {
          if (prev.find(r => r.department_id === event.data.dept_id)) return prev;
          return [...prev, { id: 'temp-'+Date.now(), department_id: event.data.dept_id, status: "analyzing" }];
        });
      }

      if (event.type === "agent_done") {
        setReports(prev => {
          // Replace placeholder or update existing
          const existing = prev.findIndex(r => r.department_id === event.data.dept_id);
          const newReport = {
            id: event.data.report_id,
            department_id: event.data.dept_id,
            content: event.data.content,
            status: "pending"
          };
          
          if (existing >= 0) {
            const next = [...prev];
            next[existing] = newReport;
            return next;
          }
          return [...prev, newReport];
        });
      }

      if (event.type === "report_validated" || event.type === "report_invalidated" || event.type === "report_modified") {
        setReports(prev => prev.map(r => {
          if (r.id === event.data.report_id) {
            return { ...r, status: event.type.replace("report_", ""), content: event.data.content || r.content };
          }
          return r;
        }));
      }

      if (event.type === "analysis_complete") {
        setPipelineState(prev => ({ ...prev, analysisComplete: true }));
      }
    }
  }, [events, ticketId]);

  const handleStatusChange = (reportId: number, status: string, actionTaken?: string, newContent?: any) => {
    setReports(prev => prev.map(r => {
      if (r.id === reportId) {
        return { ...r, status, content: newContent || r.content };
      }
      return r;
    }));
  };

  return (
    <div className="flex gap-8">
      {/* Left Column: Visual Pipeline */}
      <div className="w-1/3 min-w-[300px] border-r border-border/50 pr-8">
        <h3 className="text-lg font-bold mb-6 flex items-center gap-2">
          <Network className="h-5 w-5 text-primary" />
          Orchestration Pipeline
        </h3>
        
        <div className="space-y-6 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-border before:to-transparent">
          
          {/* Step 1 */}
          <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
            <div className="flex items-center justify-center w-10 h-10 rounded-full border-4 border-background bg-sentinel-green text-background shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10 glow-green">
              <CheckCircle2 className="w-5 h-5" />
            </div>
            <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] glass-card p-4 rounded-xl shadow-sm">
              <div className="font-bold text-sm">1. Input Received</div>
              <div className="text-xs text-muted-foreground mt-1">Event ingested via API</div>
            </div>
          </div>

          {/* Step 2 */}
          <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
            <div className="flex items-center justify-center w-10 h-10 rounded-full border-4 border-background bg-sentinel-green text-background shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10 glow-green">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] glass-card p-4 rounded-xl shadow-sm">
              <div className="font-bold text-sm">2. Security Layer</div>
              <div className="text-xs text-muted-foreground mt-1">Prompt injection scan passed</div>
            </div>
          </div>

          {/* Step 3 */}
          <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
            <div className={`flex items-center justify-center w-10 h-10 rounded-full border-4 border-background ${pipelineState.routingComplete ? 'bg-sentinel-blue glow-blue' : 'bg-muted'} text-background shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10`}>
              <Route className="w-5 h-5" />
            </div>
            <div className={`w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] glass-card p-4 rounded-xl shadow-sm ${pipelineState.routingComplete ? 'border-sentinel-blue/30' : 'opacity-50'}`}>
              <div className="font-bold text-sm">3. Orchestrator Routing</div>
              <div className="text-xs text-muted-foreground mt-1">
                {pipelineState.routingComplete ? (
                  `Mapped to ${pipelineState.targetDepts.length} departments`
                ) : (
                  <span className="flex items-center gap-2"><span className="spinner w-3 h-3 border-t-muted-foreground border-muted-foreground"></span> Routing...</span>
                )}
              </div>
            </div>
          </div>

          {/* Step 4 (Agents) */}
          <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
            <div className={`flex items-center justify-center w-10 h-10 rounded-full border-4 border-background ${pipelineState.analysisComplete ? 'bg-sentinel-green glow-green' : (pipelineState.routingComplete ? 'bg-sentinel-amber pulse-dot' : 'bg-muted')} text-background shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10`}>
              <Network className="w-5 h-5" />
            </div>
            <div className={`w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] glass-card p-4 rounded-xl shadow-sm ${pipelineState.analysisComplete ? 'border-sentinel-green/30' : (pipelineState.routingComplete ? 'border-sentinel-amber/30' : 'opacity-50')}`}>
              <div className="font-bold text-sm">4. Parallel Analysis</div>
              <div className="text-xs text-muted-foreground mt-1">
                {pipelineState.analysisComplete ? "All agents finished" : (pipelineState.routingComplete ? "Agents analyzing..." : "Waiting...")}
              </div>
            </div>
          </div>

        </div>

        <div className="mt-8 pt-6 border-t border-border/50 text-xs text-muted-foreground flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]' : 'bg-red-500'}`}></div>
          {isConnected ? "Live SSE Connection Active" : "Reconnecting to event stream..."}
        </div>
      </div>

      {/* Right Column: Reports Feed */}
      <div className="flex-1 max-w-3xl">
        <div className="bg-secondary/30 rounded-xl p-4 border border-border mb-6">
          <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-2 flex items-center gap-1.5">
            <AlertCircle className="w-3.5 h-3.5" /> Input Event Details
          </h4>
          <p className="text-sm font-mono text-foreground leading-relaxed">
            {initialPayload?.details || "No details provided"}
          </p>
        </div>

        <div className="space-y-4">
          <h3 className="text-xl font-bold mb-4">Department Reports</h3>
          
          {reports.length === 0 && !pipelineState.routingComplete && (
            <div className="text-center py-12 text-muted-foreground text-sm border border-dashed border-border rounded-xl">
              Waiting for orchestrator to assign departments...
            </div>
          )}

          {reports.map((report, idx) => (
            <div key={report.id || idx} className="animate-in fade-in slide-in-from-bottom-4 duration-500">
              {report.status === "analyzing" ? (
                <div className="glass-card rounded-xl p-5 border-sentinel-blue/20 flex items-center gap-4">
                  <div className="spinner w-5 h-5 border-2 border-sentinel-blue/20 border-t-sentinel-blue"></div>
                  <div>
                    <h4 className="font-bold text-sentinel-blue">{report.department_id}</h4>
                    <p className="text-xs text-muted-foreground">Agent is writing report...</p>
                  </div>
                </div>
              ) : (
                <ReportCard report={report} onStatusChange={handleStatusChange} />
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
