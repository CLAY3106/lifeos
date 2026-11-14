"use client"
import { useCallback, useEffect, useRef, useState } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import useSWR from "swr"
import api from "@/lib/api"
import { useRouter } from "next/navigation"
import { LeafIcon, HomeIcon, BookIcon, BriefcaseIcon, ActivityIcon, WalletIcon, LogOutIcon, UserIcon, MenuIcon, CloseIcon } from "@/components/icons"
import ThemeToggle from "@/components/ThemeToggle"
import { type ModuleKey } from "@/lib/modules"

const fetcher = (url: string) => api.get(url).then(r => r.data)

const links = [
  { href: "/dashboard", label: "Dashboard", Icon: HomeIcon, module: null as ModuleKey | null },
  { href: "/assignments", label: "Assignments", Icon: BookIcon, module: "academics" as ModuleKey },
  { href: "/jobs", label: "Jobs", Icon: BriefcaseIcon, module: "jobs" as ModuleKey },
  { href: "/fitness", label: "Fitness", Icon: ActivityIcon, module: "fitness" as ModuleKey },
  { href: "/finance", label: "Finance", Icon: WalletIcon, module: "finance" as ModuleKey },
]

function SidebarPanel({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname()
  const router = useRouter()

  // Until /auth/me resolves we show every link, so the nav never flashes empty
  // and then fills in.
  const { data: me } = useSWR("/auth/me", fetcher, { revalidateOnFocus: false })
  const activeModules = me?.active_modules

  const visibleLinks = links.filter(link => {
    if (!link.module) return true
    if (!activeModules) return true
    return activeModules.includes(link.module)
  })

  async function handleLogout() {
    await api.post("/auth/logout")
    router.push("/auth/login")
  }

  return (
    <div className="w-60 max-w-full h-full overflow-y-auto border-r border-[var(--rule)] flex flex-col bg-[var(--surface-hover)]">
      <div className="px-3 pt-4 pb-2">
        <div className="flex items-center gap-2 px-2 py-1.5 rounded hover:bg-black/[.04] transition-colors">
          <LeafIcon className="w-5 h-5 text-[var(--accent)]" />
          <span className="text-sm font-semibold text-[var(--foreground)]">LifeOS</span>
        </div>
      </div>

      <div className="px-3 mt-2">
        <p className="text-[11px] font-medium text-[var(--muted-2)] px-2 mb-1 uppercase tracking-wide">
          Workspace
        </p>
        <nav className="flex flex-col">
          {visibleLinks.map(link => {
            const active = pathname === link.href || pathname.startsWith(link.href + "/")
            const Icon = link.Icon
            return (
              <Link
                key={link.href}
                href={link.href}
                onClick={onNavigate}
                className={`group flex items-center gap-2 px-2 py-1.5 rounded text-sm transition-colors ${
                  active
                    ? "bg-black/[.06] text-[var(--foreground)] font-medium"
                    : "text-[var(--foreground)]/85 hover:bg-black/[.04]"
                }`}
              >
                <Icon className="w-[18px] h-[18px] shrink-0" />
                <span>{link.label}</span>
              </Link>
            )
          })}
        </nav>
      </div>

      <div className="flex-1" />

      <div className="px-3 pb-3 pt-2 border-t border-[var(--rule)]">
        <Link
          href="/profile"
          onClick={onNavigate}
          className={`w-full flex items-center gap-2 px-2 py-1.5 rounded text-sm transition-colors mb-1 ${
            pathname === "/profile"
              ? "bg-black/[.06] text-[var(--foreground)] font-medium"
              : "text-[var(--muted)] hover:bg-black/[.04] hover:text-[var(--foreground)]"
          }`}
        >
          <UserIcon className="w-[18px] h-[18px] shrink-0" />
          <span>Profile</span>
        </Link>
        <ThemeToggle />
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-2 px-2 py-1.5 rounded text-sm text-[var(--muted)] hover:bg-black/[.04] hover:text-[var(--foreground)] transition-colors"
        >
          <LogOutIcon className="w-[18px] h-[18px] shrink-0" />
          <span>Sign out</span>
        </button>
      </div>
    </div>
  )
}

const FOCUSABLE = 'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])'

export default function Sidebar() {
  const [open, setOpen] = useState(false)
  const menuButtonRef = useRef<HTMLButtonElement>(null)
  const drawerRef = useRef<HTMLDivElement>(null)

  const close = useCallback(() => {
    setOpen(false)
    menuButtonRef.current?.focus()
  }, [])

  useEffect(() => {
    if (!open) return
    const drawer = drawerRef.current
    drawer?.querySelector<HTMLElement>(FOCUSABLE)?.focus()

    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = "hidden"

    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") {
        close()
        return
      }
      if (e.key !== "Tab" || !drawer) return
      const items = Array.from(drawer.querySelectorAll<HTMLElement>(FOCUSABLE))
      if (items.length === 0) return
      const first = items[0]
      const last = items[items.length - 1]
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault()
        last.focus()
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault()
        first.focus()
      } else if (!drawer.contains(document.activeElement)) {
        e.preventDefault()
        first.focus()
      }
    }

    // The drawer is hidden at md and up, so drop it if the viewport grows.
    const mq = window.matchMedia("(min-width: 768px)")
    function onResize(e: MediaQueryListEvent) {
      if (e.matches) setOpen(false)
    }

    document.addEventListener("keydown", onKeyDown)
    mq.addEventListener("change", onResize)
    return () => {
      document.body.style.overflow = previousOverflow
      document.removeEventListener("keydown", onKeyDown)
      mq.removeEventListener("change", onResize)
    }
  }, [open, close])

  return (
    <>
      <aside className="hidden md:block sticky top-0 h-screen shrink-0">
        <SidebarPanel />
      </aside>

      <header className="md:hidden sticky top-0 z-30 flex items-center justify-between h-12 px-4 border-b border-[var(--rule)] bg-[var(--surface-hover)]">
        <div className="flex items-center gap-2">
          <LeafIcon className="w-5 h-5 text-[var(--accent)]" />
          <span className="text-sm font-semibold text-[var(--foreground)]">LifeOS</span>
        </div>
        <button
          ref={menuButtonRef}
          type="button"
          onClick={() => setOpen(true)}
          aria-label="Open menu"
          aria-expanded={open}
          className="-mr-2 p-2 rounded text-[var(--foreground)] hover:bg-black/[.04] transition-colors"
        >
          <MenuIcon className="w-5 h-5" />
        </button>
      </header>

      {open && (
        <div className="md:hidden fixed inset-0 z-40">
          <div className="absolute inset-0 bg-black/40" onClick={close} aria-hidden="true" />
          <div
            ref={drawerRef}
            role="dialog"
            aria-modal="true"
            aria-label="Navigation"
            className="relative h-full w-60 max-w-[85vw]"
          >
            <SidebarPanel onNavigate={() => setOpen(false)} />
            <button
              type="button"
              onClick={close}
              aria-label="Close menu"
              className="absolute top-3 right-2 p-1.5 rounded text-[var(--muted)] hover:bg-black/[.04] hover:text-[var(--foreground)] transition-colors"
            >
              <CloseIcon className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </>
  )
}
