import React from "react";

interface KPICardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  description: string;
  trend?: string;
}

export function KPICard({ title, value, icon, description, trend }: KPICardProps) {
  return (
    <div className="glass-card rounded-xl p-6 relative overflow-hidden transition-all hover:scale-[1.02] hover:border-primary/40 group">
      <div className="flex justify-between items-start mb-4">
        <div className="p-3 bg-primary/10 rounded-xl text-primary group-hover:bg-primary group-hover:text-primary-foreground transition-all duration-300">
          {React.cloneElement(icon as React.ReactElement, { className: "h-6 w-6" })}
        </div>
        {trend && (
          <span className="text-xs font-bold text-sentinel-green px-2 py-1 bg-sentinel-green/10 rounded-full">
            {trend}
          </span>
        )}
      </div>
      <div>
        <p className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">{title}</p>
        <h3 className="text-3xl font-bold mt-1 text-foreground tracking-tight">{value}</h3>
        <p className="text-xs text-muted-foreground mt-2 font-medium">{description}</p>
      </div>
      
      {/* Decorative accent */}
      <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-full -mr-16 -mt-16 blur-3xl group-hover:bg-primary/10 transition-colors"></div>
    </div>
  );
}
