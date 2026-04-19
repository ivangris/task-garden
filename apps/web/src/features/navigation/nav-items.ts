export type NavItem = {
  id: string;
  label: string;
  description: string;
};

export const navItems: NavItem[] = [
  { id: "capture", label: "Capture", description: "Fast raw capture and review queue." },
  { id: "inbox", label: "Inbox", description: "Unsorted and newly confirmed work." },
  { id: "today", label: "Today", description: "Focused work for the current day." },
  { id: "this-week", label: "This Week", description: "Planning horizon for the week." },
  { id: "projects", label: "Projects", description: "Project grouping and progress." },
  { id: "completed", label: "Completed", description: "Resolved work and recent wins." },
  { id: "settings", label: "Settings", description: "Local-first app and provider settings." }
];
