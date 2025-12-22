import type { PropsWithChildren } from "react"
import { cn } from "@/lib/utils"
import { Toaster } from "@/components/ui/toaster"
import { useFlashMessages } from "@/hooks/use-flash-messages"
import Footer from "@/layouts/partials/footer"
import Navbar from "@/layouts/partials/navbar"

type AppLayoutProps = PropsWithChildren<{ mainClassName?: string }>

export function AppLayout({ children, mainClassName }: AppLayoutProps) {
	useFlashMessages() // Auto-display flash messages as toasts

	return (
		<div className="flex min-h-screen flex-col bg-muted/20 overflow-x-hidden">
			<Toaster />
			<Navbar />
			<main className={cn("flex-1 pb-10", mainClassName)}>{children}</main>
			<Footer />
		</div>
	)
}
