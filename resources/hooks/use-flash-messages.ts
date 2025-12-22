import { usePage } from "@inertiajs/react"
import { useEffect, useRef } from "react"
import { toast } from "@/components/ui/use-toast"
import type { FullSharedProps } from "@/lib/generated/page-props"

/**
 * Hook to automatically display flash messages from Inertia page props as toasts.
 * Should be called once in your root layout component.
 *
 * Supports standard categories: success, error, info, warning
 * Each category maps to an appropriate toast variant.
 */
export function useFlashMessages() {
	// In Inertia v2, flash is at the page level, not in props
	const { flash } = usePage<FullSharedProps>()
	// Track displayed messages to prevent duplicates on re-renders
	const displayedRef = useRef<Set<string>>(new Set())

	useEffect(() => {
		if (!flash) return

		const messages: Array<{ category: string; message: string }> = []

		for (const [category, categoryMessages] of Object.entries(flash)) {
			if (!Array.isArray(categoryMessages)) continue
			for (const message of categoryMessages) {
				const key = `${category}:${message}`
				if (!displayedRef.current.has(key)) {
					messages.push({ category, message })
					displayedRef.current.add(key)
				}
			}
		}

		for (const { category, message } of messages) {
			const variant =
				category === "success"
					? "success"
					: category === "warning"
						? "warning"
						: category === "error"
							? "destructive"
							: "default"
			const title = category.charAt(0).toUpperCase() + category.slice(1)

			toast({
				title,
				description: message,
				variant,
			})
		}

		// Clear tracked messages when flash changes (new page navigation)
		return () => {
			displayedRef.current.clear()
		}
	}, [flash])
}
