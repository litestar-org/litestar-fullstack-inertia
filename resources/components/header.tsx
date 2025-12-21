import * as React from "react"
import { Container } from "@/components/container"
import { cn } from "@/lib/utils"

interface HeaderProps extends React.HTMLAttributes<HTMLDivElement> {
	title?: string
	children?: React.ReactNode
}

const Header = React.forwardRef<HTMLDivElement, HeaderProps>(({ className, title, children, ...props }, ref) => (
	<div ref={ref} className={cn("mb-12 border-b bg-background py-4 sm:py-8", className)} {...props}>
		<Container>
			<div className="flex items-center justify-between">
				<h1 className="heading-uppercase text-xl sm:text-2xl">{title}</h1>
				{children && <div className="flex items-center gap-2">{children}</div>}
			</div>
		</Container>
	</div>
))
Header.displayName = "Header"

export { Header }
