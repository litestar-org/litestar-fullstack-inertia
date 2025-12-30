import type { PropsWithChildren, ReactNode } from "react"
import { Toaster } from "@/components/ui/toaster"
import { useFlashMessages } from "@/hooks/use-flash-messages"

interface GuestLayoutProps {
	header?: string | null
	description?: string | ReactNode | null
}

export function GuestLayout({ description: _description = null, header: _header = null, children }: PropsWithChildren<GuestLayoutProps>) {
	useFlashMessages() // Auto-display flash messages as toasts

	return (
		<>
			<Toaster />
			<div className="container relative flex min-h-screen flex-col items-center justify-center md:grid md:place-items-center lg:max-w-none lg:grid-cols-2 lg:px-0">{children}</div>
		</>
	)
}
