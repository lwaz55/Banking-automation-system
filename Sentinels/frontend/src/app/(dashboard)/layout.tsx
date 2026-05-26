"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Ticket as TicketIcon,
  ShieldCheck,
  PlusCircle,
  Activity,
} from "lucide-react";

const navItems = [
  { href: "/unified", label: "Dashboard", icon: LayoutDashboard },
  { href: "/tickets", label: "Tickets", icon: TicketIcon },
  { href: "/audit", label: "Audit Log", icon: ShieldCheck },
];

function NavLink({ href, label, icon: Icon }: { href: string; label: string; icon: React.ElementType }) {
  const pathname = usePathname();
  const active = pathname === href || pathname.startsWith(href + "/");
  return (
    <Link
      href={href}
      className={`relative flex items-center gap-2 px-3 py-1.5 text-sm font-medium rounded-md transition-colors
        ${active
          ? "text-foreground bg-secondary"
          : "text-muted-foreground hover:text-foreground hover:bg-secondary/60"
        }`}
    >
      <Icon className="h-4 w-4" />
      {label}
      {active && (
        <span className="absolute bottom-0 left-3 right-3 h-[2px] rounded-full bg-sentinel-blue" />
      )}
    </Link>
  );
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col bg-background">
      <header className="sticky top-0 z-50 flex h-14 items-center border-b border-border/40 bg-background/95 px-6 backdrop-blur supports-[backdrop-filter]:bg-background/60">

        <Link href="/tickets" className="flex items-center gap-2 mr-8 group">
          <div className="relative flex items-center justify-center w-7 h-7">
            <Activity className="h-5 w-5 text-sentinel-blue transition-transform group-hover:scale-110" />
            <span className="absolute -top-0.5 -right-0.5 w-1.5 h-1.5 rounded-full bg-sentinel-green shadow-[0_0_6px_rgba(var(--sentinel-green),0.6)]" />
          </div>
          <span className="font-bold text-base tracking-tight text-foreground">
            SENTINELS
          </span>
        </Link>

        {/* Nav links */}
        <nav className="flex items-center gap-1">
          {navItems.map((item) => (
            <NavLink key={item.href} {...item} />
          ))}
        </nav>

        {/* Submit CTA removed to emphasize fully automated workflow */}
      </header>

      <main className="flex-1 p-6 md:p-8 max-w-[1600px] w-full mx-auto">
        {children}
      </main>
    </div>
  );
}