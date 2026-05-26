"use client";

import { useState } from "react";
import {
  CheckCircle2, XCircle, Edit3, Send,
  ShieldAlert, Cpu, ChevronDown, ChevronUp,
  AlertCircle, BookOpen,
} from "lucide-react";
import { validateReport, invalidateReport, modifyReport } from "@/lib/api";

type ReportCardProps = {
  report: any;
  onStatusChange: (reportId: number, status: string, actionTaken?: string, newContent?: any) => void;
};

const DEPT_LABELS: Record<string, { label: string; short: string }> = {
  DIR_RISQUE:     { label: "Risk Surveillance",      short: "Risk" },
  DIR_GGEI:       { label: "Credit Analysis — GGEI",  short: "GGEI" },
  DIR_DATA:       { label: "Analytical Data",         short: "Data" },
  DIR_SFAX:       { label: "Régionale Sfax",          short: "Sfax" },
  DIR_ALM:        { label: "Contrôle Gestion ALM",    short: "ALM" },
  DIR_GARANTIES:  { label: "Guarantees",              short: "Grtns" },
};

const STATUS_CONFIG: Record<string, { cls: string; label: string }> = {
  pending:     { cls: "badge-pending",     label: "Pending Review" },
  validated:   { cls: "badge-validated",   label: "Validated" },
  invalidated: { cls: "badge-invalidated", label: "Re-analyzing" },
  modified:    { cls: "badge-modified",    label: "Modified" },
};

function ConfidencePill({ value }: { value: string }) {
  const num = parseInt(value, 10);
  const color = num >= 80
    ? "text-sentinel-green bg-sentinel-green/10 border-sentinel-green/25"
    : num >= 50
    ? "text-sentinel-amber bg-sentinel-amber/10 border-sentinel-amber/25"
    : "text-sentinel-red bg-sentinel-red/10 border-sentinel-red/25";
  return (
    <span className={`flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-md border ${color}`}>
      <ShieldAlert className="h-3 w-3" />
      {value} confidence
    </span>
  );
}

export function ReportCard({ report, onStatusChange }: ReportCardProps) {
  const [isModifying, setIsModifying] = useState(false);
  const [expanded, setExpanded] = useState(true);
  const [editedContent, setEditedContent] = useState(JSON.stringify(report.content, null, 2));
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [jsonError, setJsonError] = useState<string | null>(null);

  const dept = DEPT_LABELS[report.department_id] ?? { label: report.department_id, short: report.department_id };
  const statusCfg = STATUS_CONFIG[report.status] ?? { cls: "bg-secondary text-secondary-foreground", label: report.status };

  const handleValidate = async () => {
    setIsSubmitting(true);
    try {
      const actionTaken = report.content?.proposed_action || "Standard protocol executed";
      await validateReport(report.id, actionTaken);
      onStatusChange(report.id, "validated", actionTaken);
    } catch (e) { console.error(e); }
    finally { setIsSubmitting(false); }
  };

  const handleInvalidate = async () => {
    setIsSubmitting(true);
    try {
      await invalidateReport(report.id);
      onStatusChange(report.id, "invalidated");
    } catch (e) { console.error(e); }
    finally { setIsSubmitting(false); }
  };

  const handleSaveModify = async () => {
    setJsonError(null);
    let parsed: any;
    try { parsed = JSON.parse(editedContent); }
    catch { setJsonError("Invalid JSON — fix formatting before saving."); return; }
    setIsSubmitting(true);
    try {
      await modifyReport(report.id, parsed);
      onStatusChange(report.id, "modified", undefined, parsed);
      setIsModifying(false);
    } catch (e) { console.error(e); }
    finally { setIsSubmitting(false); }
  };

  const borderAccent =
    report.status === "validated"   ? "border-l-sentinel-green" :
    report.status === "invalidated" ? "border-l-sentinel-red"   :
    report.status === "modified"    ? "border-l-sentinel-purple" :
    "border-l-sentinel-blue";

  return (
    <div className={`glass-card rounded-xl slide-in-up border border-border border-l-4 ${borderAccent} transition-all duration-300`}>

      {/* Header row */}
      <div
        className="flex justify-between items-center p-4 cursor-pointer select-none"
        onClick={() => setExpanded((v) => !v)}
      >
        <div className="flex items-center gap-3">
          <div className="p-1.5 bg-primary/10 rounded-lg text-primary">
            <Cpu className="h-4 w-4" />
          </div>
          <div>
            <p className="font-semibold text-sm text-foreground leading-none">{dept.label}</p>
            <p className="text-xs text-muted-foreground mt-0.5">{report.department_id}</p>
          </div>
          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${statusCfg.cls} uppercase tracking-wider`}>
            {statusCfg.label}
          </span>
        </div>
        <div className="flex items-center gap-3">
          {report.content?.confidence && (
            <ConfidencePill value={report.content.confidence} />
          )}
          {expanded
            ? <ChevronUp className="h-4 w-4 text-muted-foreground" />
            : <ChevronDown className="h-4 w-4 text-muted-foreground" />}
        </div>
      </div>

      {/* Collapsible body */}
      {expanded && (
        <div className="px-4 pb-4 space-y-4 border-t border-border/50 pt-4">

          {isModifying ? (
            <div>
              <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1.5 block">
                Edit Analysis JSON
              </label>
              <textarea
                className="w-full h-52 bg-background border border-border rounded-md p-3 text-xs font-mono focus:outline-none focus:ring-1 focus:ring-primary resize-none"
                value={editedContent}
                onChange={(e) => setEditedContent(e.target.value)}
              />
              {jsonError && (
                <p className="text-xs text-sentinel-red flex items-center gap-1.5 mt-1.5">
                  <AlertCircle className="h-3.5 w-3.5" /> {jsonError}
                </p>
              )}
              <div className="flex justify-end gap-2 mt-3">
                <button
                  onClick={() => { setIsModifying(false); setJsonError(null); }}
                  className="px-3 py-1.5 text-sm font-medium hover:bg-secondary rounded-md transition-colors"
                  disabled={isSubmitting}
                >Cancel</button>
                <button
                  onClick={handleSaveModify}
                  disabled={isSubmitting}
                  className="px-3 py-1.5 text-sm font-medium bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors flex items-center gap-2"
                >
                  <Send className="h-3.5 w-3.5" /> Save & Modify
                </button>
              </div>
            </div>
          ) : (
            <>
              {/* Analysis */}
              <div>
                <h5 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1.5">
                  Agent Analysis
                </h5>
                <p className="text-sm text-foreground leading-relaxed bg-background/50 p-3 rounded-md border border-border/50">
                  {report.content?.analysis || "No analysis provided."}
                </p>
              </div>

              {/* Proposed Action */}
              <div>
                <h5 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1.5">
                  Proposed Action
                </h5>
                <p className="text-sm font-medium text-sentinel-blue leading-relaxed bg-sentinel-blue/5 p-3 rounded-md border border-sentinel-blue/15">
                  {report.content?.proposed_action || "No action proposed."}
                </p>
              </div>

              {/* Citations */}
              {report.content?.citations && report.content.citations.length > 0 && (
                <div>
                  <h5 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                    <BookOpen className="h-3.5 w-3.5 text-sentinel-amber" /> BCT Policy Citations
                  </h5>
                  <div className="space-y-2 bg-background/30 p-3 rounded-md border border-border/50">
                    {report.content.citations.map((citation: string, i: number) => (
                      <p key={i} className="text-xs italic text-muted-foreground border-l-2 border-sentinel-amber/50 pl-3 py-1">
                        "{citation}"
                      </p>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}

          {/* Actions */}
          {report.status === "pending" && !isModifying && (
            <div className="flex gap-2 pt-2 border-t border-border/50">
              <button
                onClick={handleValidate} disabled={isSubmitting}
                className="flex-1 flex items-center justify-center gap-2 bg-sentinel-green/10 hover:bg-sentinel-green/20 text-sentinel-green border border-sentinel-green/25 px-3 py-2 rounded-lg font-medium transition-colors text-sm"
              >
                <CheckCircle2 className="h-4 w-4" /> Validate & Execute
              </button>
              <button
                onClick={handleInvalidate} disabled={isSubmitting}
                className="flex-1 flex items-center justify-center gap-2 bg-sentinel-red/10 hover:bg-sentinel-red/20 text-sentinel-red border border-sentinel-red/25 px-3 py-2 rounded-lg font-medium transition-colors text-sm"
              >
                <XCircle className="h-4 w-4" /> Reject (Re-analyze)
              </button>
              <button
                onClick={() => setIsModifying(true)} disabled={isSubmitting}
                className="flex items-center justify-center gap-2 bg-secondary hover:bg-secondary/80 text-foreground border border-border px-3 py-2 rounded-lg font-medium transition-colors text-sm"
              >
                <Edit3 className="h-4 w-4" /> Modify
              </button>
            </div>
          )}

          {report.status === "validated" && (
            <div className="pt-2 border-t border-sentinel-green/20 flex items-center gap-2 text-sm text-sentinel-green font-medium">
              <CheckCircle2 className="h-4 w-4" /> Action dispatched to Execution Agent
            </div>
          )}

          {report.status === "invalidated" && (
            <div className="pt-2 border-t border-sentinel-red/20 flex items-center gap-2 text-sm text-sentinel-red font-medium">
              <XCircle className="h-4 w-4" /> Sent back for re-analysis
            </div>
          )}
        </div>
      )}
    </div>
  );
}