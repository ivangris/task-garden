export type NavItem = {
  id: string;
  label: string;
  description: string;
  icon: string;
};

export const navItems: NavItem[] = [
  { id: "capture", label: "Capture", description: "Voice and notes.", icon: "C" },
  { id: "inbox", label: "Inbox", description: "New and manual tasks.", icon: "I" },
  { id: "planning", label: "Tasks", description: "Plan by date and project.", icon: "T" },
  { id: "projects", label: "Projects", description: "Groups and context.", icon: "P" },
  { id: "garden", label: "Garden", description: "Visible progress.", icon: "G" },
  { id: "recaps", label: "Recaps", description: "What moved.", icon: "R" },
  { id: "settings", label: "Settings", description: "Local providers.", icon: "S" },
];
