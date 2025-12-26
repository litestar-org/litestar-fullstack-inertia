import { Head } from "@inertiajs/react"
import { formatDistanceToNow } from "date-fns"
import { Container } from "@/components/container"
import { type Column, DataTable } from "@/components/data-table"
import { Header } from "@/components/header"
import { Badge } from "@/components/ui/badge"
import { AdminLayout } from "@/layouts/admin-layout"

interface AuditLogItem {
	id: string
	actorEmail: string
	action: string
	targetType: string
	targetId: string
	targetLabel: string | null
	details: Record<string, unknown> | null
	ipAddress: string | null
	createdAt: string
}

interface Props {
	logs: AuditLogItem[]
	total: number
	page?: number
	pageSize?: number
	searchString?: string
	orderBy?: string
	sortOrder?: "asc" | "desc"
}

function formatAction(action: string): string {
	return action.replace(/\./g, " ").replace(/\b\w/g, (l) => l.toUpperCase())
}

function getActionVariant(action: string): "default" | "secondary" | "destructive" | "outline" {
	if (action.includes("deleted") || action.includes("locked") || action.includes("removed") || action.includes("revoked")) {
		return "destructive"
	}
	if (action.includes("created") || action.includes("unlocked") || action.includes("verified") || action.includes("assigned")) {
		return "default"
	}
	return "secondary"
}

export default function AdminAuditList({ logs, total, page = 1, pageSize = 50, searchString, orderBy, sortOrder }: Props) {
	const columns: Column<AuditLogItem>[] = [
		{
			key: "createdAt",
			label: "Time",
			sortable: true,
			render: (log) => <span className="text-muted-foreground text-sm">{formatDistanceToNow(new Date(log.createdAt), { addSuffix: true })}</span>,
		},
		{
			key: "action",
			label: "Action",
			render: (log) => <Badge variant={getActionVariant(log.action)}>{formatAction(log.action)}</Badge>,
		},
		{
			key: "actorEmail",
			label: "Actor",
			render: (log) => <span className="font-medium">{log.actorEmail}</span>,
		},
		{
			key: "target",
			label: "Target",
			render: (log) => (
				<div>
					<p className="font-medium">{log.targetLabel || log.targetId}</p>
					<p className="text-muted-foreground text-sm capitalize">{log.targetType}</p>
				</div>
			),
		},
		{
			key: "ipAddress",
			label: "IP Address",
			render: (log) => <span className="font-mono text-muted-foreground text-sm">{log.ipAddress || "-"}</span>,
		},
		{
			key: "details",
			label: "Details",
			render: (log) =>
				log.details ? <code className="rounded bg-muted px-2 py-1 text-xs">{JSON.stringify(log.details).slice(0, 50)}...</code> : <span className="text-muted-foreground">-</span>,
		},
	]

	return (
		<>
			<Head title="Audit Log - Admin" />
			<Header title="Audit Log" />
			<Container>
				<DataTable
					data={logs}
					columns={columns}
					total={total}
					pageSize={pageSize}
					currentPage={page}
					searchPlaceholder="Search logs..."
					routeName="/admin/audit"
					searchQuery={searchString}
					sortField={orderBy}
					sortOrder={sortOrder}
					emptyMessage="No audit log entries found."
				/>
			</Container>
		</>
	)
}

AdminAuditList.layout = (page: React.ReactNode) => <AdminLayout>{page}</AdminLayout>
