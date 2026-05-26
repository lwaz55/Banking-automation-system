"use client";

import { useEffect, useState } from "react";
import { fetchAuditLog } from "@/lib/api";
import { ShieldCheck, Activity, Search, RefreshCw } from "lucide-react";

export default function AuditLogPage() {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const loadLogs = () => {
    setLoading(true);
    fetchAuditLog()
      .then(setLogs)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadLogs();
  }, []);

  const getEventColor = (eventType: string) => {
    if (eventType.includes("validated") || eventType.includes("executed") || eventType.includes("done")) return "text-sentinel-green bg-sentinel-green/10";
    if (eventType.includes("invalidated") || eventType.includes("error")) return "text-sentinel-red bg-sentinel-red/10";
    if (eventType.includes("started") || eventType.includes("modified")) return "text-sentinel-amber bg-sentinel-amber/10";
    return "text-sentinel-blue bg-sentinel-blue/10";
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight mb-2 flex items-center gap-3">
            <ShieldCheck className="h-8 w-8 text-primary" />
            Governance Audit Trail
          </h1>
          <p className="text-muted-foreground">Immutable, cryptographically chained logs of all system and human actions.</p>
        </div>
        <button 
          onClick={loadLogs}
          className="flex items-center gap-2 px-4 py-2 bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/80 transition-colors text-sm font-medium"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} /> Refresh Logs
        </button>
      </div>

      <div className="glass-card rounded-xl border border-border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="text-xs uppercase bg-secondary/50 text-muted-foreground">
              <tr>
                <th className="px-6 py-4 font-semibold">Timestamp</th>
                <th className="px-6 py-4 font-semibold">Event Type</th>
                <th className="px-6 py-4 font-semibold">Entity</th>
                <th className="px-6 py-4 font-semibold">Actor</th>
                <th className="px-6 py-4 font-semibold">Details</th>
                <th className="px-6 py-4 font-semibold">Signature (SHA-256)</th>
              </tr>
            </thead>
            <tbody>
              {loading && logs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-muted-foreground">
                    <div className="flex justify-center mb-4"><div className="spinner w-6 h-6"></div></div>
                    Loading audit trail...
                  </td>
                </tr>
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-muted-foreground">
                    No logs found.
                  </td>
                </tr>
              ) : (
                logs.map((log) => (
                  <tr key={log.id} className="border-b border-border/50 hover:bg-secondary/20 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap text-muted-foreground font-mono text-xs">
                      {new Date(log.created_at).toISOString().replace('T', ' ').substring(0, 19)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2.5 py-1 rounded-md text-xs font-semibold tracking-wide uppercase ${getEventColor(log.event_type)}`}>
                        {log.event_type.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="font-medium">{log.entity_type}</span> <span className="text-muted-foreground">#{log.entity_id}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap font-medium">
                      {log.actor === 'system' ? <span className="flex items-center gap-1.5"><Activity className="w-3.5 h-3.5 text-primary" /> System</span> : log.actor}
                    </td>
                    <td className="px-6 py-4">
                      <div className="max-w-[300px] truncate font-mono text-xs text-muted-foreground" title={JSON.stringify(log.details)}>
                        {JSON.stringify(log.details)}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="font-mono text-xs text-muted-foreground bg-background/50 px-2 py-1 rounded border border-border/50" title={log.signature}>
                        {log.signature.substring(0, 16)}...
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
