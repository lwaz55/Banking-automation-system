"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { submitEvent } from "@/lib/api";
import { Send, AlertTriangle, ChevronDown, Loader2, Info, ChevronRight, Building2 } from "lucide-react";

const EVENT_TYPES = [
  {
    value: "early_warning",
    label: "Early Warning Signal",
    description: "Customer shows early signs of financial stress before defaulting (e.g. declining revenue, missed payments starting).",
    departments: ["Risk Surveillance", "Data & Analytics"],
    color: "text-sentinel-amber",
  },
  {
    value: "loan_restructuring",
    label: "Loan Restructuring",
    description: "The bank or customer initiates a change to existing loan terms (rate, duration, moratorium).",
    departments: ["Risk Surveillance", "ALM & Control", "Guarantees"],
    color: "text-sentinel-blue",
  },
  {
    value: "voluntary_restructuring",
    label: "Voluntary Restructuring",
    description: "Customer proactively requests restructuring before entering delinquency. Positive signal — customer is cooperative.",
    departments: ["Risk Surveillance", "Regional Branch", "Guarantees"],
    color: "text-sentinel-green",
  },
  {
    value: "credit_review",
    label: "Credit Review",
    description: "Periodic or triggered review of a customer's creditworthiness and IFRS 9 classification.",
    departments: ["Risk Surveillance", "Data & Analytics", "Credit Analysis (GGEI)"],
    color: "text-sentinel-blue",
  },
  {
    value: "npl_alert",
    label: "NPL Alert",
    description: "Customer has crossed into Non-Performing Loan territory (DPD > 90 days). Immediate provisioning required.",
    departments: ["Risk Surveillance", "Recovery", "Guarantees"],
    color: "text-sentinel-red",
  },
  {
    value: "collection_action",
    label: "Collection Action",
    description: "Formal recovery process initiated against a delinquent customer (letters, legal, asset seizure).",
    departments: ["Recovery", "Guarantees", "Risk Surveillance"],
    color: "text-sentinel-red",
  },
  {
    value: "provisioning_update",
    label: "Provisioning Update",
    description: "Update to ECL provisioning amounts under IFRS 9, triggered by stage change or new financial data.",
    departments: ["Risk Surveillance", "ALM & Control", "Data & Analytics"],
    color: "text-sentinel-purple",
  },
  {
    value: "regulatory_inquiry",
    label: "Regulatory Inquiry",
    description: "BCT (Banque Centrale de Tunisie) or an external auditor is requesting information about a customer or exposure.",
    departments: ["Risk Surveillance", "Data & Analytics", "ALM & Control"],
    color: "text-sentinel-purple",
  },
  {
    value: "customer_complaint",
    label: "Customer Complaint",
    description: "A formal complaint has been lodged, requiring investigation and potential loan review.",
    departments: ["Risk Surveillance", "Regional Branch"],
    color: "text-sentinel-amber",
  },
  {
    value: "dora_event",
    label: "DORA Event",
    description: "A digital operational resilience event (IT system failure, cyber incident) impacting banking operations.",
    departments: ["Data & Analytics", "Risk Surveillance"],
    color: "text-sentinel-amber",
  },
  {
    value: "it_incident",
    label: "IT Incident",
    description: "Technology disruption affecting core banking systems, data integrity, or customer transactions.",
    departments: ["Data & Analytics"],
    color: "text-sentinel-amber",
  },
  {
    value: "audit_request",
    label: "Audit Request",
    description: "Internal or external audit requiring a full dossier of a customer's credit history and documentation.",
    departments: ["Risk Surveillance", "Data & Analytics", "Guarantees"],
    color: "text-sentinel-purple",
  },
];

const EXAMPLE_PAYLOAD = {
  customer_id: "CUST-OPT-007",
  event_type: "voluntary_restructuring",
  details: "Optima Retail Group (SME, TPME segment, loan TND 1.2M) has proactively contacted STB requesting a voluntary restructuring of their loan before entering delinquency. Company context: operates 4 retail outlets in Sfax medina. Revenue dropped 28% post-COVID recovery stall and due to new competing mall opening nearby. Current DPD: 0 (customer is proactive). Request: 6-month principal moratorium + interest rate reduction from 9.5% to 7.5%. Financial docs submitted: latest balance sheet shows equity still positive (TND 340K) but cash flow is negative for last 2 quarters. Guarantees: personal guarantee from owner + stock pledge (TND 280K). Branch manager (Dir. Régionale Sfax) recommends the restructuring as the owner is cooperative and sector recovery likely within 12-18 months.",
};

export default function SubmitEventPage() {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState(EXAMPLE_PAYLOAD);
  const [showGuide, setShowGuide] = useState(false);

  const selectedType = EVENT_TYPES.find(t => t.value === formData.event_type);
  const charCount = formData.details.length;
  const charLimit = 8000;
  const charPct = Math.min((charCount / charLimit) * 100, 100);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);
    try {
      const res = await submitEvent({ source: "dashboard", payload: formData });
      if (res.ticket_id) {
        router.push(`/tickets/${res.ticket_id}`);
      }
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.message || "Submission failed — check backend logs.";
      setError(msg);
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight mb-1">Submit New Event</h1>
        <p className="text-muted-foreground text-sm">
          Trigger the multi-agent pipeline. Input passes through the Security Layer before routing.
        </p>
      </div>

      {/* Event Type Guide Toggle */}
      <button
        onClick={() => setShowGuide(!showGuide)}
        className="w-full flex items-center justify-between px-4 py-3 glass-card rounded-xl border border-border hover:border-primary/40 transition-colors text-sm"
      >
        <div className="flex items-center gap-2 text-muted-foreground">
          <Info className="w-4 h-4 text-primary" />
          <span>Not sure which event type to choose? Click to see the guide</span>
        </div>
        <ChevronDown className={`w-4 h-4 text-muted-foreground transition-transform ${showGuide ? "rotate-180" : ""}`} />
      </button>

      {/* Event Type Guide Panel */}
      {showGuide && (
        <div className="glass-card rounded-xl border border-border overflow-hidden">
          <div className="px-5 py-3 border-b border-border/50 bg-secondary/20">
            <h3 className="font-bold text-sm">Event Type Guide</h3>
            <p className="text-xs text-muted-foreground mt-0.5">Click an event type to select it and auto-fill the form.</p>
          </div>
          <div className="divide-y divide-border/30 max-h-[480px] overflow-y-auto">
            {EVENT_TYPES.map((type) => (
              <button
                key={type.value}
                onClick={() => {
                  setFormData(prev => ({ ...prev, event_type: type.value }));
                  setShowGuide(false);
                }}
                className={`w-full text-left px-5 py-4 hover:bg-secondary/30 transition-colors group ${
                  formData.event_type === type.value ? "bg-primary/5 border-l-2 border-primary" : ""
                }`}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className={`font-semibold text-sm mb-1 ${type.color}`}>{type.label}</div>
                    <p className="text-xs text-muted-foreground leading-relaxed">{type.description}</p>
                    <div className="flex flex-wrap gap-1.5 mt-2">
                      {type.departments.map(dept => (
                        <span key={dept} className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-secondary text-[10px] font-medium text-muted-foreground border border-border/50">
                          <Building2 className="w-2.5 h-2.5" />
                          {dept}
                        </span>
                      ))}
                    </div>
                  </div>
                  <ChevronRight className="w-4 h-4 text-muted-foreground shrink-0 mt-0.5 group-hover:text-primary transition-colors" />
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="glass-card rounded-xl p-6 border border-border">
        <form onSubmit={handleSubmit} className="space-y-5">

          {/* Customer ID */}
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Customer ID</label>
            <input
              type="text"
              value={formData.customer_id}
              onChange={(e) => setFormData({ ...formData, customer_id: e.target.value })}
              placeholder="e.g. CUST-XYZ-001"
              maxLength={64}
              className="w-full bg-background border border-border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-sentinel-blue/40 focus:border-sentinel-blue/50 transition-colors"
              required
            />
          </div>

          {/* Event Type */}
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Event Type</label>
            <div className="relative">
              <select
                value={formData.event_type}
                onChange={(e) => setFormData({ ...formData, event_type: e.target.value })}
                className="w-full appearance-none bg-background border border-border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-sentinel-blue/40 focus:border-sentinel-blue/50 transition-colors pr-10"
              >
                {EVENT_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
              <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
            </div>

            {/* Inline description of selected event type */}
            {selectedType && (
              <div className="flex gap-2 px-3 py-2.5 rounded-lg bg-secondary/50 border border-border/50">
                <Info className={`w-3.5 h-3.5 shrink-0 mt-0.5 ${selectedType.color}`} />
                <div className="flex-1">
                  <p className="text-xs text-muted-foreground leading-relaxed">{selectedType.description}</p>
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {selectedType.departments.map(dept => (
                      <span key={dept} className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-secondary text-[10px] font-medium text-muted-foreground border border-border/50">
                        <Building2 className="w-2.5 h-2.5" />
                        {dept}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Details */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium">Event Details</label>
              <span className={`text-xs font-mono tabular-nums ${charCount > charLimit * 0.9 ? "text-sentinel-red" : "text-muted-foreground"}`}>
                {charCount.toLocaleString()} / {charLimit.toLocaleString()}
              </span>
            </div>
            <textarea
              value={formData.details}
              onChange={(e) => setFormData({ ...formData, details: e.target.value })}
              className="w-full h-52 bg-background border border-border rounded-md p-3 text-sm leading-relaxed focus:outline-none focus:ring-2 focus:ring-sentinel-blue/40 focus:border-sentinel-blue/50 transition-colors resize-none"
              maxLength={charLimit}
              placeholder="Describe the event in detail: customer name, loan amounts, DPD, financial context, reason for the event..."
              required
            />
            <div className="h-0.5 rounded-full bg-border overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-300"
                style={{
                  width: `${charPct}%`,
                  backgroundColor: charPct > 90 ? "var(--sentinel-red)" : charPct > 70 ? "var(--sentinel-amber)" : "var(--sentinel-blue)",
                }}
              />
            </div>
            <p className="text-xs text-muted-foreground">
              💡 <strong>Tip:</strong> Include the customer name, loan amount (in TND), DPD days, and the specific situation. The more detail you provide, the better the AI analysis.
            </p>
          </div>

          {/* Error */}
          {error && (
            <div className="bg-sentinel-red/10 border border-sentinel-red/25 rounded-md p-3 flex gap-2.5 text-sm text-sentinel-red">
              <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {/* Warning */}
          <div className="bg-sentinel-amber/8 border border-sentinel-amber/20 rounded-md p-3 flex gap-2.5 text-sm text-sentinel-amber">
            <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
            <div>
              <p className="font-medium">This will activate the orchestrator.</p>
              <p className="opacity-75 text-xs mt-0.5">Relevant department agents will be assigned and begin analysis immediately.</p>
            </div>
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full bg-sentinel-blue hover:bg-sentinel-blue/90 disabled:opacity-60 text-white font-medium py-2.5 rounded-lg flex justify-center items-center gap-2 transition-all text-sm"
          >
            {isSubmitting ? (
              <><Loader2 className="w-4 h-4 animate-spin" /> Launching pipeline...</>
            ) : (
              <><Send className="w-4 h-4" /> Launch Pipeline</>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}