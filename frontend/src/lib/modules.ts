// Module keys shared by the onboarding wizard, the sidebar filter, and the
// /auth/me payload (active_modules). One definition so the frontend cannot
// drift away from the backend's allowed values.

export type ModuleKey = "academics" | "jobs" | "fitness" | "finance"

export const ALL_MODULES: ModuleKey[] = ["academics", "jobs", "fitness", "finance"]

// Sidebar href for each module key. Used to hide links for inactive modules.
export const MODULE_HREFS: Record<ModuleKey, string> = {
  academics: "/assignments",
  jobs: "/jobs",
  fitness: "/fitness",
  finance: "/finance",
}
