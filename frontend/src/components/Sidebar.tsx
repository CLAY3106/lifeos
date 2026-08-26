"use client"
import Link from "next/link"
import { usePathname } from "next/navigation"
import api from "@/lib/api"
import { useRouter } from "next/navigation"
import { LeafIcon, HomeIcon, BookIcon, BriefcaseIcon, ActivityIcon, WalletIcon, LogOutIcon } from "@/components/icons"

const links = [
  { href: "/dashboard", label: "Dashboard", Icon: HomeIcon },
  { href: "/assignments", label: "Assignments", Icon: BookIcon },
  { href: "/jobs", label: "Jobs", Icon: BriefcaseIcon },
  { href: "/fitness", label: "Fitness", Icon: ActivityIcon },
  { href: "/finance", label: "Finance", Icon: WalletIcon },
]

export default function Sidebar() {
  const pathname = usePathname()
  const router = useRouter()

  async function handleLogout() {
    await api.post("/auth/logout")
    router.push("/auth/login")
  }

  return (
    <aside className="w-60 min-h-screen border-r border-[var(--rule)] flex flex-col bg-[var(--surface-hover)]">
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
          {links.map(link => {
            const active = pathname === link.href || pathname.startsWith(link.href + "/")
            const Icon = link.Icon
            return (
              <Link
                key={link.href}
                href={link.href}
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
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-2 px-2 py-1.5 rounded text-sm text-[var(--muted)] hover:bg-black/[.04] hover:text-[var(--foreground)] transition-colors"
        >
          <LogOutIcon className="w-[18px] h-[18px] shrink-0" />
          <span>Sign out</span>
        </button>
      </div>
    </aside>
  )
}
