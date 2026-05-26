"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { fetchTickets } from "@/lib/api";
import { Ticket, Clock, ArrowRight, Activity, AlertCircle, Search, X } from "lucide-react";

export default function TicketsPage() {
  const [tickets, setTickets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<"all" | "open" | "analysis_complete">("all");
  const [newTicketFlash, setNewTicketFlash] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);

  const loadTickets = () => {
    fetchTickets()
      .then(setTickets)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadTickets();

    // SSE: auto-refresh when new tickets are created or analysis completes
    const es = new EventSource("http://127.0.0.1:8000/api/v1/stream/events");
    eventSourceRef.current = es;

    es.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data);
        if (
          parsed.type === "ticket_created" ||
          parsed.type === "analysis_complete"
        ) {
          setNewTicketFlash(true);
          setTimeout(() => setNewTicketFlash(false), 2000);
          loadTickets();
        }
      } catch {}
    };

    return () => es.close();
  }, []);

  // Client-side filtering
  const filtered = tickets
    .filter((t) => {
      const matchSearch = search === "" || t.customer_id.toLowerCase().includes(search.toLowerCase());
      const matchStatus = statusFilter === "all" || t.status === statusFilter;
      return matchSearch && matchStatus;
    });

  const STATUS_TABS = [
    { key: "all", label: "All" },
    { key: "open", label: "Open" },
    { key: "analysis_complete", label: "Complete" },
  ] as const;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold tracking-tight mb-2 flex items-center gap-3">
            Active Tickets
            {newTicketFlash && (
              <span className="text-xs font-normal px-2.5 py-1 rounded-full bg-sentinel-green/15 text-sentinel-green border border-sentinel-green/30 animate-pulse">
                Updated
              </span>
            )}
          </h1>
          <p className="text-muted-foreground">Manage and monitor orchestration pipelines for all events.</p>
        </div>
        <Link
          href="/submit"
          className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg font-medium text-sm hover:bg-primary/90 transition-colors shadow-lg shadow-primary/20"
        >
          + New Event
        </Link>
      </div>

      {/* Search + Filter bar */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search by customer ID..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-secondary/50 border border-border rounded-lg pl-9 pr-9 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary/50 transition-colors"
          />
          {search && (
            <button onClick={() => setSearch("")} className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground">
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
        <div className="flex gap-1 p-1 bg-secondary/50 rounded-lg border border-border">
          {STATUS_TABS.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setStatusFilter(tab.key)}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-colors ${
                statusFilter === tab.key
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="spinner w-8 h-8" />
        </div>
      ) : tickets.length === 0 ? (
        <div className="text-center py-20 glass-card rounded-xl border border-dashed border-border">
          <Ticket className="w-12 h-12 text-muted-foreground mx-auto mb-4 opacity-50" />
          <h3 className="text-lg font-semibold mb-2">No active tickets</h3>
          <p className="text-muted-foreground mb-6">Submit a new event to trigger the multi-agent system.</p>
          <Link href="/submit" className="bg-primary text-primary-foreground px-4 py-2 rounded-lg font-medium inline-block">
            Submit Event
          </Link>
        </div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-16 glass-card rounded-xl border border-dashed border-border">
          <Search className="w-10 h-10 text-muted-foreground mx-auto mb-3 opacity-40" />
          <p className="text-muted-foreground">No tickets match your search.</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {filtered.map(ticket => (
            <div key={ticket.id} className="glass-card rounded-xl p-5 hover:border-primary/50 transition-colors flex flex-col md:flex-row md:items-center gap-6 group">

              <div className="flex items-center gap-4 md:w-1/4">
                <div className={`p-3 rounded-xl ${ticket.status === 'open' ? 'bg-sentinel-amber/10 text-sentinel-amber' : 'bg-sentinel-blue/10 text-sentinel-blue'}`}>
                  {ticket.status === 'open' ? <Activity className="w-6 h-6" /> : <AlertCircle className="w-6 h-6" />}
                </div>
                <div>
                  <Link href={`/tickets/${ticket.id}`} className="font-bold text-lg leading-none mb-1 text-foreground hover:text-primary transition-colors block">
                    TKT-{String(ticket.id).padStart(4, '0')}
                  </Link>
                  <p className="text-sm text-muted-foreground flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {new Date(ticket.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>

              <div className="md:w-1/3">
                <div className="text-xs text-muted-foreground uppercase tracking-wider font-semibold mb-1">Customer</div>
                <Link
                  href={`/customers/${encodeURIComponent(ticket.customer_id)}`}
                  className="font-medium text-primary hover:underline text-sm"
                  onClick={(e) => e.stopPropagation()}
                >
                  {ticket.customer_id}
                </Link>
              </div>

              <div className="md:w-1/4">
                <div className="text-xs text-muted-foreground uppercase tracking-wider font-semibold mb-1">Progress</div>
                <div className="flex items-center gap-2">
                  <div className="flex-1 h-2 bg-secondary rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary rounded-full transition-all"
                      style={{ width: ticket.report_count ? `${(ticket.validated_count / ticket.report_count) * 100}%` : '0%' }}
                    />
                  </div>
                  <span className="text-xs font-medium">{ticket.validated_count}/{ticket.report_count}</span>
                </div>
              </div>

              <div className="flex items-center justify-end flex-1">
                <span className={`px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wide border ${
                  ticket.status === 'open'
                    ? 'bg-sentinel-amber/10 border-sentinel-amber/30 text-sentinel-amber'
                    : 'bg-sentinel-blue/10 border-sentinel-blue/30 text-sentinel-blue'
                }`}>
                  {ticket.status.replace("_", " ")}
                </span>
                <Link href={`/tickets/${ticket.id}`}>
                  <ArrowRight className="w-5 h-5 ml-4 text-muted-foreground group-hover:text-primary transition-colors transform group-hover:translate-x-1" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
