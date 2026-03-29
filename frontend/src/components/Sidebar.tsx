"use client"
import Link from "next/link"
import { usePathname } from "next/navigation"
import api from "@/lib/api"
import { useRouter } from "next/navigation"

const links = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/assignments", label: "Assignments" },
  { href: "/jobs", label: "Jobs" },
  { href: "/fitness", label: "Fitness" },
  { href: "/finance", label: "Finance" },
]

export default function Sidebar() {
  const pathname = usePathname()
  const router = useRouter()

  async function handleLogout() {
    await api.post("/auth/logout")
    router.push("/auth/login")
  }

  return (
    <aside className="w-48 min-h-screen bg-white border-r flex flex-col py-6 px-4">
      <h1 className="text-xl font-bold mb-8">LifeOS</h1>
      <nav className="flex flex-col gap-1 flex-1">
        {links.map(link => (
          <Link
            key={link.href}
            href={link.href}
            className={`px-3 py-2 rounded text-sm font-medium transition-colors ${
              pathname === link.href
                ? "bg-black text-white"
                : "text-gray-600 hover:bg-gray-100"
            }`}
          >
            {link.label}
          </Link>
        ))}
      </nav>
      <button
        onClick={handleLogout}
        className="text-sm text-gray-500 hover:text-black text-left px-3 py-2"
      >
        Logout
      </button>
    </aside>
  )
}