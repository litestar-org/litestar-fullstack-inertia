import { Head, Link, router } from "@inertiajs/react"
import { formatDistanceToNow } from "date-fns"
import { Lock, MoreHorizontal, Plus, Shield, ShieldCheck, Trash2, Unlock, UserCog } from "lucide-react"
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
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { AdminLayout } from "@/layouts/admin-layout"
import { getGravatarUrl, getInitials } from "@/lib/utils"

interface AdminUserListItem {
	id: string
	email: string
	name: string | null
	isActive: boolean
	isSuperuser: boolean
	isVerified: boolean
	isTwoFactorEnabled: boolean
	roleNames: string[]
	teamCount: number
	createdAt: string | null
	avatarUrl: string | null
}

interface Props {
	users: AdminUserListItem[]
	total: number
	page?: number
	pageSize?: number
	searchString?: string
	orderBy?: string
	sortOrder?: "asc" | "desc"
}

export default function AdminUsersList({ users, total, page = 1, pageSize = 25, searchString, orderBy, sortOrder }: Props) {
	const columns: Column<AdminUserListItem>[] = [
		{
			key: "user",
			label: "User",
			render: (user) => (
				<div className="flex items-center gap-3">
					<Avatar className="h-8 w-8">
						<AvatarImage src={user.avatarUrl ?? getGravatarUrl(user.email)} />
						<AvatarFallback>{getInitials(user.email)}</AvatarFallback>
					</Avatar>
					<div>
						<div className="font-medium">{user.name || user.email}</div>
						{user.name && <div className="text-muted-foreground text-sm">{user.email}</div>}
					</div>
				</div>
			),
		},
		{
			key: "status",
			label: "Status",
			render: (user) => (
				<div className="flex flex-wrap gap-1">
					{user.isSuperuser && (
						<Badge className="bg-purple-500">
							<Shield className="mr-1 h-3 w-3" />
							Superuser
						</Badge>
					)}
					{user.isVerified ? (
						<Badge variant="outline" className="border-green-500 text-green-600">
							<ShieldCheck className="mr-1 h-3 w-3" />
							Verified
						</Badge>
					) : (
						<Badge variant="outline" className="border-yellow-500 text-yellow-600">
							Unverified
						</Badge>
					)}
					{!user.isActive && (
						<Badge variant="destructive">
							<Lock className="mr-1 h-3 w-3" />
							Locked
						</Badge>
					)}
					{user.isTwoFactorEnabled && <Badge variant="secondary">MFA</Badge>}
				</div>
			),
		},
		{
			key: "roleNames",
			label: "Roles",
			render: (user) => (
				<div className="flex flex-wrap gap-1">
					{user.roleNames.map((role) => (
						<Badge key={role} variant="secondary">
							{role}
						</Badge>
					))}
				</div>
			),
		},
		{
			key: "teamCount",
			label: "Teams",
			sortable: true,
			render: (user) => user.teamCount,
		},
		{
			key: "createdAt",
			label: "Created",
			sortable: true,
			render: (user) => (user.createdAt ? formatDistanceToNow(new Date(user.createdAt), { addSuffix: true }) : "-"),
		},
		{
			key: "actions",
			label: "",
			render: (user) => (
				<DropdownMenu>
					<DropdownMenuTrigger asChild>
						<Button variant="ghost" size="icon">
							<MoreHorizontal className="h-4 w-4" />
						</Button>
					</DropdownMenuTrigger>
					<DropdownMenuContent align="end">
						<DropdownMenuItem asChild>
							<Link href={`/admin/users/${user.id}`}>
								<UserCog className="mr-2 h-4 w-4" />
								View Details
							</Link>
						</DropdownMenuItem>
						<DropdownMenuSeparator />
						{user.isActive ? (
							<DropdownMenuItem onClick={() => router.post(`/admin/users/${user.id}/lock/`)} className="text-destructive">
								<Lock className="mr-2 h-4 w-4" />
								Lock Account
							</DropdownMenuItem>
						) : (
							<DropdownMenuItem onClick={() => router.post(`/admin/users/${user.id}/unlock/`)}>
								<Unlock className="mr-2 h-4 w-4" />
								Unlock Account
							</DropdownMenuItem>
						)}
						<AlertDialog>
							<AlertDialogTrigger asChild>
								<DropdownMenuItem onSelect={(e) => e.preventDefault()} className="text-destructive">
									<Trash2 className="mr-2 h-4 w-4" />
									Delete User
								</DropdownMenuItem>
							</AlertDialogTrigger>
							<AlertDialogContent>
								<AlertDialogHeader>
									<AlertDialogTitle>Delete User</AlertDialogTitle>
									<AlertDialogDescription>Are you sure you want to delete {user.email}? This action cannot be undone.</AlertDialogDescription>
								</AlertDialogHeader>
								<AlertDialogFooter>
									<AlertDialogCancel>Cancel</AlertDialogCancel>
									<AlertDialogAction className="bg-destructive text-destructive-foreground hover:bg-destructive/90" onClick={() => router.delete(`/admin/users/${user.id}/`)}>
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
			<Head title="Users - Admin" />
			<Header title="Users">
				<Link href="/admin/users/create">
					<Button>
						<Plus className="mr-2 h-4 w-4" />
						Create User
					</Button>
				</Link>
			</Header>
			<Container>
				<DataTable
					data={users}
					columns={columns}
					total={total}
					pageSize={pageSize}
					currentPage={page}
					searchPlaceholder="Search users..."
					routeName="/admin/users"
					searchQuery={searchString}
					sortField={orderBy}
					sortOrder={sortOrder}
				/>
			</Container>
		</>
	)
}

AdminUsersList.layout = (page: React.ReactNode) => <AdminLayout>{page}</AdminLayout>
