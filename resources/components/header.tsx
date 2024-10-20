import { Container } from "@/components/container"
import { cn } from "@/lib/utils"
import * as React from "react"

const Header = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(({ className, ...props }, ref) => (
	<div ref={ref} className={cn("mb-12 border-b bg-background py-4 sm:py-8", className)} {...props}>
		<Container>
			<h1 className="font-semibold text-xl tracking-tight sm:text-2xl">{props.title}</h1>
		</Container>
	</div>
))
Header.displayName = "Header"

export { Header }
