import { Head, Link } from "@inertiajs/react"
import { formatDistanceToNow } from "date-fns"
import { Activity, Building2, Clock, ShieldCheck, UserPlus, Users } from "lucide-react"
import { Container } from "@/components/container"
import { Header } from "@/components/header"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { AdminLayout } from "@/layouts/admin-layout"

interface AuditLogItem {
	id: string
	actorEmail: string
	action: string
	targetType: string
	targetId: string
	targetLabel: string | null
	createdAt: string
}

interface AdminStats {
	totalUsers: number
	activeUsers: number
	verifiedUsers: number
	totalTeams: number
	recentSignups: number
}

interface Props {
	stats: AdminStats
	recentLogs: AuditLogItem[]
}

function StatCard({ title, value, description, icon: Icon }: { title: string; value: number; description?: string; icon: React.ElementType }) {
	return (
		<Card>
			<CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
				<CardTitle className="font-medium text-sm">{title}</CardTitle>
				<Icon className="h-4 w-4 text-muted-foreground" />
			</CardHeader>
			<CardContent>
				<div className="font-bold text-2xl">{value.toLocaleString()}</div>
				{description && <p className="text-muted-foreground text-xs">{description}</p>}
			</CardContent>
		</Card>
	)
}

function formatAction(action: string): string {
	return action.replace(/\./g, " ").replace(/\b\w/g, (l) => l.toUpperCase())
}

function getActionVariant(action: string): "default" | "secondary" | "destructive" | "outline" {
	if (action.includes("deleted") || action.includes("locked") || action.includes("removed")) {
		return "destructive"
	}
	if (action.includes("created") || action.includes("unlocked") || action.includes("verified")) {
		return "default"
	}
	return "secondary"
}

export default function AdminDashboard({ stats, recentLogs }: Props) {
	return (
		<>
			<Head title="Admin Dashboard" />
			<Header title="Admin Dashboard" />
			<Container>
				<div className="space-y-8">
					{/* Stats Cards */}
					<div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
						<StatCard title="Total Users" value={stats.totalUsers} icon={Users} />
						<StatCard title="Active Users" value={stats.activeUsers} description="Accounts not locked" icon={ShieldCheck} />
						<StatCard title="Verified Users" value={stats.verifiedUsers} description="Email verified" icon={ShieldCheck} />
						<StatCard title="Total Teams" value={stats.totalTeams} icon={Building2} />
						<StatCard title="Recent Signups" value={stats.recentSignups} description="Last 7 days" icon={UserPlus} />
					</div>

					{/* Quick Links */}
					<div className="grid gap-4 md:grid-cols-3">
						<Link href="/admin/users">
							<Card className="transition-shadow hover:shadow-md">
								<CardHeader>
									<CardTitle className="flex items-center gap-2">
										<Users className="h-5 w-5" />
										Manage Users
									</CardTitle>
									<CardDescription>View, create, and manage user accounts</CardDescription>
								</CardHeader>
							</Card>
						</Link>
						<Link href="/admin/teams">
							<Card className="transition-shadow hover:shadow-md">
								<CardHeader>
									<CardTitle className="flex items-center gap-2">
										<Building2 className="h-5 w-5" />
										Manage Teams
									</CardTitle>
									<CardDescription>View and manage all teams</CardDescription>
								</CardHeader>
							</Card>
						</Link>
						<Link href="/admin/audit">
							<Card className="transition-shadow hover:shadow-md">
								<CardHeader>
									<CardTitle className="flex items-center gap-2">
										<Activity className="h-5 w-5" />
										View Audit Log
									</CardTitle>
									<CardDescription>Track all admin actions</CardDescription>
								</CardHeader>
							</Card>
						</Link>
					</div>

					{/* Recent Activity */}
					<Card>
						<CardHeader>
							<CardTitle className="flex items-center gap-2">
								<Clock className="h-5 w-5" />
								Recent Activity
							</CardTitle>
							<CardDescription>Latest admin actions</CardDescription>
						</CardHeader>
						<CardContent>
							{recentLogs.length === 0 ? (
								<p className="py-4 text-center text-muted-foreground">No recent activity</p>
							) : (
								<div className="space-y-4">
									{recentLogs.map((log) => (
										<div key={log.id} className="flex items-center justify-between border-b pb-3 last:border-0">
											<div className="flex items-center gap-4">
												<Badge variant={getActionVariant(log.action)}>{formatAction(log.action)}</Badge>
												<div>
													<p className="font-medium text-sm">{log.targetLabel || log.targetId}</p>
													<p className="text-muted-foreground text-xs">by {log.actorEmail}</p>
												</div>
											</div>
											<span className="text-muted-foreground text-sm">{formatDistanceToNow(new Date(log.createdAt), { addSuffix: true })}</span>
										</div>
									))}
								</div>
							)}
						</CardContent>
					</Card>
				</div>
			</Container>
		</>
	)
}

AdminDashboard.layout = (page: React.ReactNode) => <AdminLayout>{page}</AdminLayout>
