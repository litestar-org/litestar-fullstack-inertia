import { Link, usePage } from "@inertiajs/react"
import { ArrowLeft, Building2, ClipboardList, LayoutDashboard, Users } from "lucide-react"
import type { PropsWithChildren } from "react"
import { Toaster } from "@/components/ui/toaster"
import { useFlashMessages } from "@/hooks/use-flash-messages"
import Footer from "@/layouts/partials/footer"
import Navbar from "@/layouts/partials/navbar"
import type { FullSharedProps } from "@/lib/generated/page-props"
import { isCurrentRoute } from "@/lib/generated/routes"
import { cn } from "@/lib/utils"

interface AdminSidebarItem {
	label: string
	href: string
	icon: React.ElementType
	active: boolean
}

function AdminSidebar() {
	const sidebarItems: AdminSidebarItem[] = [
		{
			label: "Dashboard",
			href: "/admin",
			icon: LayoutDashboard,
			active: isCurrentRoute("admin.dashboard"),
		},
		{
			label: "Users",
			href: "/admin/users",
			icon: Users,
			active: isCurrentRoute("admin.users.*"),
		},
		{
			label: "Teams",
			href: "/admin/teams",
			icon: Building2,
			active: isCurrentRoute("admin.teams.*"),
		},
		{
			label: "Audit Log",
			href: "/admin/audit",
			icon: ClipboardList,
			active: isCurrentRoute("admin.audit.*"),
		},
	]

	return (
		<aside className="hidden w-64 border-r bg-background lg:block">
			<div className="flex h-full flex-col">
				<div className="border-b p-4">
					<div className="flex items-center gap-2">
						<LayoutDashboard className="h-5 w-5 text-primary" />
						<span className="font-semibold">Admin Panel</span>
					</div>
				</div>

				<nav className="flex-1 space-y-1 p-4">
					{sidebarItems.map((item) => (
						<Link
							key={item.label}
							href={item.href}
							className={cn(
								"flex items-center gap-3 rounded-lg px-3 py-2 font-medium text-sm transition-colors",
								item.active ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-muted hover:text-foreground",
							)}
						>
							<item.icon className="h-4 w-4" />
							{item.label}
						</Link>
					))}
				</nav>

				<div className="border-t p-4">
					<Link href="/" className="flex items-center gap-2 text-muted-foreground text-sm hover:text-foreground">
						<ArrowLeft className="h-4 w-4" />
						Back to App
					</Link>
				</div>
			</div>
		</aside>
	)
}

type AdminLayoutProps = PropsWithChildren<{ mainClassName?: string }>

export function AdminLayout({ children, mainClassName }: AdminLayoutProps) {
	useFlashMessages()

	return (
		<div className="flex min-h-screen flex-col bg-muted/20 overflow-x-hidden">
			<Toaster />
			<Navbar />
			<div className="flex flex-1">
				<AdminSidebar />
				<main className={cn("flex-1 pb-10", mainClassName)}>{children}</main>
			</div>
			<Footer />
		</div>
	)
}
