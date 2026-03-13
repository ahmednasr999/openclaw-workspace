import { CalendarEvent, Contact } from "@/lib/types";

export const navGroups = [
  { label: "Workspace", items: [
    { href: "/dashboard", label: "Dashboard", short: "DB" },
    { href: "/tasks", label: "Board", short: "BD" },
    { href: "/calendar", label: "Calendar", short: "CL" },
    { href: "/projects", label: "Projects", short: "PJ" },
  ] },
  { label: "Knowledge", items: [
    { href: "/memory", label: "Memory", short: "ME" },
    { href: "/docs", label: "Docs", short: "DC" },
    { href: "/team", label: "Team", short: "TM" },
    { href: "/office", label: "Office", short: "OF" },
  ] },
  { label: "Operations", items: [
    { href: "/handoff-gate", label: "Handoff Gate", short: "HG" },
    { href: "/job-radar", label: "Job Radar", short: "JR" },
    { href: "/linkedin-generator", label: "LinkedIn", short: "LI" },
    { href: "/content-factory", label: "Factory", short: "CF" },
    { href: "/settings", label: "Settings", short: "ST" },
  ] },
];

export const navItems = navGroups.flatMap((g) => g.items);

export const defaultEvents: CalendarEvent[] = [
  { id: "e1", title: "VP application review", date: "2026-03-04", time: "09:00", category: "task", source: "Tasks", details: "Review open applications and assign next actions." },
  { id: "e2", title: "LinkedIn post publish", date: "2026-03-04", time: "13:00", category: "content", source: "Content", details: "Publish approved leadership post." },
  { id: "e3", title: "Delphi interview prep", date: "2026-03-05", time: "17:00", category: "meeting", source: "Meetings", details: "Finalize interview examples." },
  { id: "e4", title: "OpenClaw cron health check", date: "2026-03-06", time: "08:00", category: "automation", source: "Automations", details: "Confirm last successful runs." },
];

export const contacts: Contact[] = [
  { id: "c1", name: "Maha Al Fahim", role: "VP Transformation", company: "GCC Health Systems", email: "maha@example.com", category: "Executive", notes: "Strong sponsor potential." },
  { id: "c2", name: "Khaled Nassar", role: "Talent Partner", company: "Delta Search", email: "khaled@example.com", category: "Hiring", notes: "Prefers concise weekly profile updates." },
  { id: "c3", name: "Rana Omar", role: "Founder", company: "Strategy Labs", email: "rana@example.com", category: "Partner", notes: "Potential collaboration on AI PMO advisory." },
  { id: "c4", name: "Youssef Amin", role: "Automation Engineer", company: "OpenClaw Ops", email: "youssef@example.com", category: "Team", notes: "Owner of monitoring automations." },
];
