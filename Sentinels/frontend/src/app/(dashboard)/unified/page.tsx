import { UnifiedDashboard } from "@/components/dashboards/unified-dashboard";

export default function UnifiedDashboardPage() {
  return (
    <div className="flex-col md:flex">
      <div className="flex-1 space-y-4">
        <div className="flex items-center justify-between space-y-2">
          <h2 className="text-3xl font-bold tracking-tight">Unified Operator Dashboard</h2>
        </div>
        <UnifiedDashboard />
      </div>
    </div>
  );
}
