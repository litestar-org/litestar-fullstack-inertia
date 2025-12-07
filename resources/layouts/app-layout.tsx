import type { PropsWithChildren } from "react"
import { Toaster } from "@/components/ui/toaster"
import Footer from "@/layouts/partials/footer"
import Navbar from "@/layouts/partials/navbar"

export function AppLayout({ children }: PropsWithChildren) {
	return (
		<div className="h-screen bg-muted/20">
			<Toaster />
			<Navbar />
			<main>
				<div className="mb-auto">{children}</div>
			</main>
			<Footer />
		</div>
	)
}
