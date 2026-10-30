"use client"
import { useEffect, useState } from "react"
import { SunIcon, MoonIcon } from "@/components/icons"

export default function ThemeToggle() {
  const [theme, setTheme] = useState<"light" | "dark">("light")

  useEffect(() => {
    // Reading persisted theme after mount is intentional: doing it during
    // render would cause a server/client hydration mismatch. This effect
    // synchronizes React state with an external system (localStorage + DOM).
    const saved = localStorage.getItem("theme") as "light" | "dark" | null
    if (saved) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setTheme(saved)
      document.documentElement.setAttribute("data-theme", saved)
    } else if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
      setTheme("dark")
      document.documentElement.setAttribute("data-theme", "dark")
    }
  }, [])

  function toggle() {
    const next = theme === "light" ? "dark" : "light"
    setTheme(next)
    localStorage.setItem("theme", next)
    document.documentElement.setAttribute("data-theme", next)
  }

  return (
    <button
      onClick={toggle}
      className="w-full flex items-center gap-2 px-2 py-1.5 rounded text-sm text-[var(--muted)] hover:bg-black/[.04] hover:text-[var(--foreground)] transition-colors"
      aria-label="Toggle theme"
    >
      {theme === "light" ? (
        <MoonIcon className="w-[18px] h-[18px] shrink-0" />
      ) : (
        <SunIcon className="w-[18px] h-[18px] shrink-0" />
      )}
      <span>{theme === "light" ? "Dark mode" : "Light mode"}</span>
    </button>
  )
}
