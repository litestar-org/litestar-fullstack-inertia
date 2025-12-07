import { MoonIcon, ServerIcon, SunIcon } from "lucide-react"
import { useTheme } from "@/components/theme-provider"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

export function ThemeToggle() {
	const { theme, setTheme } = useTheme()

	return (
		<div className="flex items-center gap-x-1 [&_button]:rounded-full [&_svg]:size-4">
			<Button size="icon" variant="ghost" className={cn(theme === "light" ? "bg-secondary" : "bg-background")} onClick={() => setTheme("light")}>
				<SunIcon />
			</Button>
			<Button size="icon" variant="ghost" className={cn(theme === "dark" ? "bg-secondary" : "bg-background")} onClick={() => setTheme("dark")}>
				<MoonIcon />
			</Button>
			<Button size="icon" variant="ghost" className={cn(theme === "system" ? "bg-secondary" : "bg-background")} onClick={() => setTheme("system")}>
				<ServerIcon />
			</Button>
		</div>
	)
}
