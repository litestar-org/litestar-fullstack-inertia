import type { HTMLAttributes } from "react"
import { cn } from "@/lib/utils"

export function InputError({ message, className = "", ...props }: HTMLAttributes<HTMLParagraphElement> & { message?: string }) {
	return message ? (
		<p {...props} className={cn("text-destructive text-sm", className)}>
			{message}
		</p>
	) : null
}
