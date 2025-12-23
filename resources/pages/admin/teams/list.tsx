import { Head, Link, router } from "@inertiajs/react"
import { formatDistanceToNow } from "date-fns"
import { Building2, MoreHorizontal, Trash2, Users } from "lucide-react"
import { Container } from "@/components/container"
import { type Column, DataTable } from "@/components/data-table"
import { Header } from "@/components/header"
import {
	AlertDialog,
	AlertDialogAction,
	AlertDialogCancel,
	AlertDialogContent,
	AlertDialogDescription,
	AlertDialogFooter,
	AlertDialogHeader,
	AlertDialogTitle,
	AlertDialogTrigger,
} from "@/components/ui/alert-dialog"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { AdminLayout } from "@/layouts/admin-layout"

interface AdminTeamListItem {
	id: string
	name: string
	slug: string
	description: string | null
	isActive: boolean
	memberCount: number
	ownerEmail: string | null
	createdAt: string | null
}

interface Props {
	teams: AdminTeamListItem[]
	total: number
	page?: number
	pageSize?: number
	searchString?: string
	orderBy?: string
	sortOrder?: "asc" | "desc"
}

export default function AdminTeamsList({ teams, total, page = 1, pageSize = 25, searchString, orderBy, sortOrder }: Props) {
	const columns: Column<AdminTeamListItem>[] = [
		{
			key: "team",
			label: "Team",
			render: (team) => (
				<div className="flex items-center gap-3">
					<div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
						<Building2 className="h-5 w-5 text-primary" />
					</div>
					<div>
						<div className="font-medium">{team.name}</div>
						<div className="text-muted-foreground text-sm">{team.slug}</div>
					</div>
				</div>
			),
		},
		{
			key: "description",
			label: "Description",
			render: (team) => <span className="line-clamp-1 max-w-xs text-muted-foreground text-sm">{team.description || "-"}</span>,
		},
		{
			key: "ownerEmail",
			label: "Owner",
			render: (team) => team.ownerEmail || "-",
		},
		{
			key: "memberCount",
			label: "Members",
			sortable: true,
			render: (team) => (
				<div className="flex items-center gap-1">
					<Users className="h-4 w-4 text-muted-foreground" />
					{team.memberCount}
				</div>
			),
		},
		{
			key: "status",
			label: "Status",
			render: (team) =>
				team.isActive ? (
					<Badge variant="outline" className="border-green-500 text-green-600">
						Active
					</Badge>
				) : (
					<Badge variant="destructive">Inactive</Badge>
				),
		},
		{
			key: "createdAt",
			label: "Created",
			sortable: true,
			render: (team) => (team.createdAt ? formatDistanceToNow(new Date(team.createdAt), { addSuffix: true }) : "-"),
		},
		{
			key: "actions",
			label: "",
			render: (team) => (
				<DropdownMenu>
					<DropdownMenuTrigger asChild>
						<Button variant="ghost" size="icon">
							<MoreHorizontal className="h-4 w-4" />
						</Button>
					</DropdownMenuTrigger>
					<DropdownMenuContent align="end">
						<DropdownMenuItem asChild>
							<Link href={`/admin/teams/${team.id}`}>
								<Building2 className="mr-2 h-4 w-4" />
								View Details
							</Link>
						</DropdownMenuItem>
						<DropdownMenuSeparator />
						<AlertDialog>
							<AlertDialogTrigger asChild>
								<DropdownMenuItem onSelect={(e) => e.preventDefault()} className="text-destructive">
									<Trash2 className="mr-2 h-4 w-4" />
									Delete Team
								</DropdownMenuItem>
							</AlertDialogTrigger>
							<AlertDialogContent>
								<AlertDialogHeader>
									<AlertDialogTitle>Delete Team</AlertDialogTitle>
									<AlertDialogDescription>Are you sure you want to delete "{team.name}"? This will remove all team members and cannot be undone.</AlertDialogDescription>
								</AlertDialogHeader>
								<AlertDialogFooter>
									<AlertDialogCancel>Cancel</AlertDialogCancel>
									<AlertDialogAction className="bg-destructive text-destructive-foreground hover:bg-destructive/90" onClick={() => router.delete(`/admin/teams/${team.id}/`)}>
										Delete
									</AlertDialogAction>
								</AlertDialogFooter>
							</AlertDialogContent>
						</AlertDialog>
					</DropdownMenuContent>
				</DropdownMenu>
			),
		},
	]

	return (
		<>
			<Head title="Teams - Admin" />
			<Header title="Teams" />
			<Container>
				<DataTable
					data={teams}
					columns={columns}
					total={total}
					pageSize={pageSize}
					currentPage={page}
					searchPlaceholder="Search teams..."
					routeName="/admin/teams"
					searchQuery={searchString}
					sortField={orderBy}
					sortOrder={sortOrder}
				/>
			</Container>
		</>
	)
}

AdminTeamsList.layout = (page: React.ReactNode) => <AdminLayout>{page}</AdminLayout>
