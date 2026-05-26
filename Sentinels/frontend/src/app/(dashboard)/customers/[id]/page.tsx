"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { fetchCustomerProfile } from "@/lib/api";
import Link from "next/link";
import {
  ArrowLeft, User, Building2, TrendingUp, TrendingDown,
  Minus, FileText, CheckCircle2, Clock, AlertTriangle, Activity
} from "lucide-react";

const RISK_COLORS = [
  "",
  "text-sentinel-green",
  "text-sentinel-green",
  "text-sentinel-amber",
  "text-sentinel-amber",
  "text-sentinel-red",
];

const RISK_LABELS = ["", "Very Low", "Low", "Medium", "High", "Critical"];

const SEGMENT_COLORS: Record<string, string> = {
  GGEI: "bg-sentinel-purple/10 text-sentinel-purple border-sentinel-purple/30",
  SME: "bg-sentinel-blue/10 text-sentinel-blue border-sentinel-blue/30",
  TPME: "bg-sentinel-amber/10 text-sentinel-amber border-sentinel-amber/30",
  Retail: "bg-sentinel-green/10 text-sentinel-green border-sentinel-green/30",
};

export default function CustomerProfilePage() {
  const params = useParams();
  const router = useRouter();
  const customerId = decodeURIComponent(params.id as string);
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCustomerProfile(customerId)
      .then(setProfile)
      .catch(() => router.push("/tickets"))
      .finally(() => setLoading(false));
  }, [customerId, router]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="spinner w-8 h-8" />
      </div>
    );
  }

  if (!profile) return null;

  const riskStage = Math.min(Math.max(profile.risk_stage, 1), 5);
  const riskColor = RISK_COLORS[riskStage];
  const riskLabel = RISK_LABELS[riskStage];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => router.back()}
          className="p-2 bg-secondary text-secondary-foreground rounded-full hover:bg-secondary/80 transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <div className="flex items-center gap-3 mb-1">
            <div className="p-2 rounded-lg bg-primary/10">
              <User className="w-5 h-5 text-primary" />
            </div>
            <h1 className="text-3xl font-bold tracking-tight">{profile.name || profile.id}</h1>
            <span className={`px-2.5 py-1 rounded-full text-xs font-bold uppercase tracking-wider border ${SEGMENT_COLORS[profile.segment] || "bg-muted text-muted-foreground border-border"}`}>
              {profile.segment}
            </span>
          </div>
          <p className="text-muted-foreground font-mono text-sm pl-11">{profile.id}</p>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass-card rounded-xl p-5 border border-border/50">
          <div className="text-xs text-muted-foreground uppercase tracking-wider font-semibold mb-1">Loan Size</div>
          <div className="text-2xl font-bold">
            {(profile.loan_size / 1_000_000).toFixed(1)}M
          </div>
          <div className="text-xs text-muted-foreground mt-0.5">TND</div>
        </div>

        <div className="glass-card rounded-xl p-5 border border-border/50">
          <div className="text-xs text-muted-foreground uppercase tracking-wider font-semibold mb-1">Risk Stage</div>
          <div className={`text-2xl font-bold ${riskColor}`}>{riskStage} / 5</div>
          <div className={`text-xs mt-0.5 ${riskColor}`}>{riskLabel}</div>
        </div>

        <div className="glass-card rounded-xl p-5 border border-border/50">
          <div className="text-xs text-muted-foreground uppercase tracking-wider font-semibold mb-1">Total Tickets</div>
          <div className="text-2xl font-bold">{profile.total_tickets}</div>
          <div className="text-xs text-muted-foreground mt-0.5">{profile.open_tickets} open</div>
        </div>

        <div className="glass-card rounded-xl p-5 border border-border/50">
          <div className="text-xs text-muted-foreground uppercase tracking-wider font-semibold mb-1">Validated Reports</div>
          <div className="text-2xl font-bold text-sentinel-green">{profile.validated_reports}</div>
          <div className="text-xs text-muted-foreground mt-0.5">actions confirmed</div>
        </div>
      </div>

      {/* Core Banking System (CBS) Metrics */}
      <div className="glass-card rounded-xl border border-border/50 overflow-hidden">
        <div className="px-6 py-4 border-b border-border/50 flex items-center gap-2 bg-secondary/10">
          <Building2 className="w-4 h-4 text-primary" />
          <h2 className="font-bold text-lg">Core Banking Metrics</h2>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 divide-y md:divide-y-0 md:divide-x divide-border/30">
          <div className="p-5">
            <div className="text-xs text-muted-foreground uppercase tracking-wider font-semibold mb-1">Days Past Due</div>
            <div className={`text-2xl font-bold ${profile.dpd > 90 ? "text-sentinel-red" : profile.dpd > 30 ? "text-sentinel-amber" : "text-sentinel-green"}`}>
              {profile.dpd} <span className="text-sm font-normal text-muted-foreground">days</span>
            </div>
          </div>
          <div className="p-5">
            <div className="text-xs text-muted-foreground uppercase tracking-wider font-semibold mb-1">Payment Status</div>
            <div className={`text-lg font-bold capitalize ${profile.payment_status === "default" ? "text-sentinel-red" : profile.payment_status === "late" ? "text-sentinel-amber" : "text-sentinel-green"}`}>
              {profile.payment_status}
            </div>
          </div>
          <div className="p-5">
            <div className="text-xs text-muted-foreground uppercase tracking-wider font-semibold mb-1">IFRS 9 Stage</div>
            <div className={`text-2xl font-bold ${profile.ifrs9_stage === 3 ? "text-sentinel-red" : profile.ifrs9_stage === 2 ? "text-sentinel-amber" : "text-sentinel-green"}`}>
              Stage {profile.ifrs9_stage}
            </div>
          </div>
          <div className="p-5">
            <div className="text-xs text-muted-foreground uppercase tracking-wider font-semibold mb-1">Outstanding Balance</div>
            <div className="text-xl font-bold font-mono">
              {profile.outstanding_balance.toLocaleString()} <span className="text-sm font-normal text-muted-foreground font-sans">TND</span>
            </div>
          </div>
        </div>
        {profile.history && (
          <div className="px-6 py-4 border-t border-border/30 bg-secondary/5">
            <div className="text-xs text-muted-foreground uppercase tracking-wider font-semibold mb-1.5 flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5" /> CBS Notes
            </div>
            <p className="text-sm text-muted-foreground leading-relaxed">{profile.history}</p>
          </div>
        )}
      </div>

      {/* Ticket History */}
      <div className="glass-card rounded-xl border border-border/50 overflow-hidden">
        <div className="px-6 py-4 border-b border-border/50 flex items-center gap-2">
          <Activity className="w-4 h-4 text-primary" />
          <h2 className="font-bold text-lg">Ticket History</h2>
          <span className="ml-auto text-xs text-muted-foreground">{profile.ticket_history.length} total</span>
        </div>

        {profile.ticket_history.length === 0 ? (
          <div className="py-16 text-center text-muted-foreground">
            <FileText className="w-10 h-10 mx-auto mb-3 opacity-30" />
            <p>No tickets found for this customer.</p>
          </div>
        ) : (
          <div className="divide-y divide-border/30">
            {profile.ticket_history.map((t: any) => {
              const progress = t.report_count > 0 ? (t.validated_count / t.report_count) * 100 : 0;
              return (
                <Link
                  key={t.ticket_id}
                  href={`/tickets/${t.ticket_id}`}
                  className="flex items-center gap-6 px-6 py-4 hover:bg-secondary/20 transition-colors group"
                >
                  {/* Icon */}
                  <div className={`p-2 rounded-lg shrink-0 ${
                    t.status === "open"
                      ? "bg-sentinel-amber/10 text-sentinel-amber"
                      : "bg-sentinel-blue/10 text-sentinel-blue"
                  }`}>
                    {t.status === "open" ? <Clock className="w-4 h-4" /> : <CheckCircle2 className="w-4 h-4" />}
                  </div>

                  {/* Ticket info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-bold text-sm">TKT-{String(t.ticket_id).padStart(4, "0")}</span>
                      <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase tracking-widest border ${
                        t.status === "open"
                          ? "bg-sentinel-amber/10 border-sentinel-amber/30 text-sentinel-amber"
                          : "bg-sentinel-blue/10 border-sentinel-blue/30 text-sentinel-blue"
                      }`}>{t.status.replace("_", " ")}</span>
                    </div>
                    <div className="text-xs text-muted-foreground capitalize">
                      {t.event_type.replace(/_/g, " ")} · {new Date(t.created_at).toLocaleDateString()}
                    </div>
                  </div>

                  {/* Progress */}
                  <div className="hidden md:block w-32">
                    <div className="flex justify-between text-xs text-muted-foreground mb-1">
                      <span>Reports</span>
                      <span>{t.validated_count}/{t.report_count}</span>
                    </div>
                    <div className="h-1.5 bg-secondary rounded-full overflow-hidden">
                      <div
                        className="h-full bg-primary rounded-full transition-all"
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                  </div>

                  <ArrowLeft className="w-4 h-4 text-muted-foreground rotate-180 group-hover:text-primary transition-colors shrink-0" />
                </Link>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
