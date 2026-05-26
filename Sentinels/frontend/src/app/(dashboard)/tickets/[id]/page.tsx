"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { fetchTicket, exportTicketPDF } from "@/lib/api";
import { LivePipeline } from "@/components/live-pipeline";
import { ArrowLeft, FileText, Download, User } from "lucide-react";
import Link from "next/link";
import { CopilotChat } from "@/components/copilot-chat";

export default function TicketDetailPage() {
  const params = useParams();
  const router = useRouter();
  const ticketId = params.id as string;
  const [ticket, setTicket] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    fetchTicket(ticketId)
      .then(setTicket)
      .catch(() => {
        // Handle 404 or error
        router.push("/tickets");
      })
      .finally(() => setLoading(false));
  }, [ticketId, router]);

  const handleExport = async () => {
    setExporting(true);
    try {
      await exportTicketPDF(ticketId);
    } catch (error) {
      console.error("Export failed:", error);
      alert("Failed to export PDF report.");
    } finally {
      setExporting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="spinner w-8 h-8"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/tickets" className="p-2 bg-secondary text-secondary-foreground rounded-full hover:bg-secondary/80 transition-colors">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-3xl font-bold tracking-tight">TKT-{String(ticket.id).padStart(4, '0')}</h1>
              <span className={`px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wide border ${
                ticket.status === 'open' ? 'bg-sentinel-amber/10 border-sentinel-amber/30 text-sentinel-amber' : 'bg-sentinel-blue/10 border-sentinel-blue/30 text-sentinel-blue'
              }`}>
                {ticket.status}
              </span>
            </div>
            <p className="text-muted-foreground flex items-center gap-2 mt-1">
              <FileText className="w-4 h-4" />
              Customer:{" "}
              <Link
                href={`/customers/${encodeURIComponent(ticket.customer_id)}`}
                className="font-medium text-primary hover:underline flex items-center gap-1"
              >
                <User className="w-3.5 h-3.5" />
                {ticket.customer_id}
              </Link>
            </p>
          </div>
        </div>
        
        <button
          onClick={handleExport}
          disabled={exporting}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-all font-medium shadow-lg shadow-primary/20 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {exporting ? (
            <div className="spinner w-4 h-4 border-primary-foreground/20 border-t-primary-foreground"></div>
          ) : (
            <Download className="w-4 h-4" />
          )}
          {exporting ? "Generating PDF..." : "Export PDF Report"}
        </button>
      </div>

      {/* The main live pipeline component handles the rest */}
      <LivePipeline ticketId={ticketId} initialPayload={ticket.input_payload} />

      {/* AI Copilot Chat sliding drawer and floating toggle */}
      <CopilotChat ticketId={ticketId} />
    </div>
  );
}
