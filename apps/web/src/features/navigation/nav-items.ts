export type NavItem = {
  id: string;
  label: string;
  description: string;
  icon: string;
};

export const navItems: NavItem[] = [
  { id: "capture", label: "Capture", description: "Thoughts in, structure later.", icon: "◌" },
  { id: "inbox", label: "Inbox", description: "Fresh work waiting for shape.", icon: "◎" },
  { id: "today", label: "Today", description: "What deserves attention now.", icon: "◔" },
  { id: "this-week", label: "This Week", description: "A calmer view of the next stretch.", icon: "◗" },
  { id: "projects", label: "Projects", description: "Grouped work with light context.", icon: "▣" },
  { id: "completed", label: "Completed", description: "Closed loops and visible momentum.", icon: "✦" },
  { id: "garden", label: "Garden", description: "A living read on care and recovery.", icon: "✿" },
  { id: "recaps", label: "Recaps", description: "Grounded snapshots of progress.", icon: "✧" },
  { id: "settings", label: "Settings", description: "Providers, local mode, and device basics.", icon: "⚙" }
];
