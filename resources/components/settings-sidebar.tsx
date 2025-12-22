import type { LucideIcon } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { cn } from "@/lib/utils"

export interface SettingsSidebarItem {
	id: string
	label: string
	icon: LucideIcon
	description?: string
}

interface SettingsSidebarProps {
	title: string
	items: SettingsSidebarItem[]
	activeId?: string
	onItemClick?: (id: string) => void
}

export function SettingsSidebar({ title, items, activeId, onItemClick }: SettingsSidebarProps) {
	const handleClick = (id: string) => {
		if (onItemClick) {
			onItemClick(id)
		}
		// Scroll to the section
		const element = document.getElementById(id)
		if (element) {
			element.scrollIntoView({ behavior: "smooth", block: "start" })
		}
	}

	return (
		<Card>
			<CardHeader>
				<CardTitle>{title}</CardTitle>
			</CardHeader>
			<CardContent className="space-y-1">
				{items.map((item) => {
					const Icon = item.icon
					return (
						<button
							key={item.id}
							type="button"
							onClick={() => handleClick(item.id)}
							className={cn(
								"flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left text-sm transition-colors",
								"hover:bg-muted",
								activeId === item.id && "bg-muted font-medium",
							)}
						>
							<Icon className="h-4 w-4 text-muted-foreground" />
							<div className="flex-1">
								<span>{item.label}</span>
								{item.description && <p className="text-muted-foreground text-xs">{item.description}</p>}
							</div>
						</button>
					)
				})}
			</CardContent>
		</Card>
	)
}
