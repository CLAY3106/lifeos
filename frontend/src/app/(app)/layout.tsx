import Sidebar from "@/components/Sidebar"
import { Toaster } from "react-hot-toast"

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen bg-[var(--background)]">
      <Sidebar />
      <main className="flex-1 overflow-x-hidden">
        {children}
      </main>
      <Toaster
        position="bottom-right"
        toastOptions={{
          style: {
            background: "rgb(24, 24, 27)",
            color: "#fafafa",
            border: "1px solid #27272a",
            borderRadius: "8px",
            fontSize: "13px",
          },
        }}
      />
    </div>
  )
}
