import { Head, Link, router, useForm } from "@inertiajs/react"
import { format } from "date-fns"
import { ArrowLeft, Building2, KeyRound, Lock, Shield, ShieldCheck, Trash2, Unlock, UserX } from "lucide-react"
import { useState } from "react"
import { Container } from "@/components/container"
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
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Separator } from "@/components/ui/separator"
import { Switch } from "@/components/ui/switch"
import { useToast } from "@/components/ui/use-toast"
import { AdminLayout } from "@/layouts/admin-layout"
import { getGravatarUrl, getInitials } from "@/lib/utils"

interface UserRoleInfo {
	id: string
	roleId: string
	roleSlug: string
	roleName: string
	assignedAt: string
}

interface UserTeamInfo {
	teamId: string
	teamName: string
	teamSlug: string
	role: string
	isOwner: boolean
}

interface RoleOption {
	id: string
	slug: string
	name: string
}

interface AdminUserDetail {
	id: string
	email: string
	name: string | null
	isActive: boolean
	isSuperuser: boolean
	isVerified: boolean
	isTwoFactorEnabled: boolean
	hasPassword: boolean
	roles: UserRoleInfo[]
	teams: UserTeamInfo[]
	createdAt: string | null
	updatedAt: string | null
	avatarUrl: string | null
}

interface Props {
	user: AdminUserDetail
	availableRoles: RoleOption[]
}

export default function AdminUserDetail({ user, availableRoles }: Props) {
	const { toast } = useToast()
	const [selectedRole, setSelectedRole] = useState<string>("")

	const { data, setData, patch, processing } = useForm({
		email: user.email,
		name: user.name || "",
		isSuperuser: user.isSuperuser,
	})

	const handleSubmit = (e: React.FormEvent) => {
		e.preventDefault()
		patch(`/admin/users/${user.id}/`, {
			preserveScroll: true,
			onSuccess: () => {
				toast({ description: "User updated successfully.", variant: "success" })
			},
		})
	}

	const handleAssignRole = () => {
		if (!selectedRole) return
		router.post(
			`/admin/users/${user.id}/roles/`,
			{ roleId: selectedRole },
			{
				preserveScroll: true,
				onSuccess: () => {
					setSelectedRole("")
					toast({ description: "Role assigned successfully.", variant: "success" })
				},
			},
		)
	}

	const handleRevokeRole = (userRoleId: string) => {
		router.delete(`/admin/users/${user.id}/roles/${userRoleId}/`, {
			preserveScroll: true,
			onSuccess: () => {
				toast({ description: "Role revoked successfully.", variant: "success" })
			},
		})
	}

	const assignableRoles = availableRoles.filter((role) => !user.roles.some((r) => r.roleId === role.id))

	return (
		<>
			<Head title={`${user.name || user.email} - Admin`} />
			<Header title={user.name || user.email}>
				<Link href="/admin/users">
					<Button variant="outline">
						<ArrowLeft className="mr-2 h-4 w-4" />
						Back to Users
					</Button>
				</Link>
			</Header>
			<Container>
				<div className="grid gap-6 lg:grid-cols-3">
					{/* User Info */}
					<div className="lg:col-span-2">
						<Card>
							<CardHeader>
								<div className="flex items-center gap-4">
									<Avatar className="h-16 w-16">
										<AvatarImage src={user.avatarUrl ?? getGravatarUrl(user.email)} />
										<AvatarFallback className="text-lg">{getInitials(user.email)}</AvatarFallback>
									</Avatar>
									<div>
										<CardTitle>{user.name || user.email}</CardTitle>
										<CardDescription>{user.email}</CardDescription>
									</div>
								</div>
							</CardHeader>
							<CardContent>
								<form onSubmit={handleSubmit} className="space-y-4">
									<div className="grid gap-4 md:grid-cols-2">
										<div className="space-y-2">
											<Label htmlFor="email">Email</Label>
											<Input id="email" value={data.email} onChange={(e) => setData("email", e.target.value)} />
										</div>
										<div className="space-y-2">
											<Label htmlFor="name">Name</Label>
											<Input id="name" value={data.name} onChange={(e) => setData("name", e.target.value)} />
										</div>
									</div>

									<div className="flex items-center space-x-2">
										<Switch id="superuser" checked={data.isSuperuser} onCheckedChange={(checked) => setData("isSuperuser", checked)} />
										<Label htmlFor="superuser">Superuser</Label>
									</div>

									<Button type="submit" disabled={processing}>
										{processing ? "Saving..." : "Save Changes"}
									</Button>
								</form>
							</CardContent>
						</Card>

						{/* Roles */}
						<Card className="mt-6">
							<CardHeader>
								<CardTitle>Roles</CardTitle>
								<CardDescription>Manage user roles</CardDescription>
							</CardHeader>
							<CardContent>
								<div className="space-y-4">
									{user.roles.length > 0 ? (
										<div className="space-y-2">
											{user.roles.map((role) => (
												<div key={role.id} className="flex items-center justify-between rounded-md border p-3">
													<div>
														<p className="font-medium">{role.roleName}</p>
														<p className="text-muted-foreground text-sm">Assigned {format(new Date(role.assignedAt), "MMM d, yyyy")}</p>
													</div>
													<Button variant="outline" size="sm" onClick={() => handleRevokeRole(role.id)}>
														Remove
													</Button>
												</div>
											))}
										</div>
									) : (
										<p className="text-muted-foreground">No roles assigned</p>
									)}

									{assignableRoles.length > 0 && (
										<>
											<Separator />
											<div className="flex gap-2">
												<Select value={selectedRole} onValueChange={setSelectedRole}>
													<SelectTrigger className="flex-1">
														<SelectValue placeholder="Select a role to assign" />
													</SelectTrigger>
													<SelectContent>
														{assignableRoles.map((role) => (
															<SelectItem key={role.id} value={role.id}>
																{role.name}
															</SelectItem>
														))}
													</SelectContent>
												</Select>
												<Button onClick={handleAssignRole} disabled={!selectedRole}>
													Assign
												</Button>
											</div>
										</>
									)}
								</div>
							</CardContent>
						</Card>

						{/* Teams */}
						<Card className="mt-6">
							<CardHeader>
								<CardTitle className="flex items-center gap-2">
									<Building2 className="h-5 w-5" />
									Team Memberships
								</CardTitle>
							</CardHeader>
							<CardContent>
								{user.teams.length > 0 ? (
									<div className="space-y-2">
										{user.teams.map((team) => (
											<div key={team.teamId} className="flex items-center justify-between rounded-md border p-3">
												<div>
													<p className="font-medium">{team.teamName}</p>
													<div className="flex items-center gap-2 text-muted-foreground text-sm">
														<Badge variant="secondary" className="capitalize">
															{team.isOwner ? "Owner" : team.role}
														</Badge>
													</div>
												</div>
												<Link href={`/admin/teams/${team.teamId}`}>
													<Button variant="outline" size="sm">
														View Team
													</Button>
												</Link>
											</div>
										))}
									</div>
								) : (
									<p className="text-muted-foreground">Not a member of any teams</p>
								)}
							</CardContent>
						</Card>
					</div>

					{/* Sidebar */}
					<div className="space-y-6">
						{/* Status */}
						<Card>
							<CardHeader>
								<CardTitle>Status</CardTitle>
							</CardHeader>
							<CardContent className="space-y-4">
								<div className="flex flex-wrap gap-2">
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
									{user.isTwoFactorEnabled && <Badge variant="secondary">MFA Enabled</Badge>}
									{user.hasPassword && (
										<Badge variant="outline">
											<KeyRound className="mr-1 h-3 w-3" />
											Has Password
										</Badge>
									)}
								</div>

								<Separator />

								<div className="space-y-2 text-sm">
									<p>
										<span className="text-muted-foreground">Created:</span> {user.createdAt ? format(new Date(user.createdAt), "MMM d, yyyy 'at' h:mm a") : "-"}
									</p>
									<p>
										<span className="text-muted-foreground">Updated:</span> {user.updatedAt ? format(new Date(user.updatedAt), "MMM d, yyyy 'at' h:mm a") : "-"}
									</p>
								</div>
							</CardContent>
						</Card>

						{/* Actions */}
						<Card>
							<CardHeader>
								<CardTitle>Actions</CardTitle>
							</CardHeader>
							<CardContent className="space-y-2">
								{user.isActive ? (
									<Button variant="outline" className="w-full" onClick={() => router.post(`/admin/users/${user.id}/lock/`)}>
										<Lock className="mr-2 h-4 w-4" />
										Lock Account
									</Button>
								) : (
									<Button variant="outline" className="w-full" onClick={() => router.post(`/admin/users/${user.id}/unlock/`)}>
										<Unlock className="mr-2 h-4 w-4" />
										Unlock Account
									</Button>
								)}

								{!user.isVerified && (
									<Button variant="outline" className="w-full" onClick={() => router.post(`/admin/users/${user.id}/verify/`)}>
										<ShieldCheck className="mr-2 h-4 w-4" />
										Verify Email
									</Button>
								)}

								{user.isVerified && (
									<Button variant="outline" className="w-full" onClick={() => router.post(`/admin/users/${user.id}/unverify/`)}>
										<UserX className="mr-2 h-4 w-4" />
										Unverify Email
									</Button>
								)}

								<Separator />

								<AlertDialog>
									<AlertDialogTrigger asChild>
										<Button variant="destructive" className="w-full">
											<Trash2 className="mr-2 h-4 w-4" />
											Delete User
										</Button>
									</AlertDialogTrigger>
									<AlertDialogContent>
										<AlertDialogHeader>
											<AlertDialogTitle>Delete User</AlertDialogTitle>
											<AlertDialogDescription>
												Are you sure you want to delete {user.email}? This action cannot be undone and will remove all associated data.
											</AlertDialogDescription>
										</AlertDialogHeader>
										<AlertDialogFooter>
											<AlertDialogCancel>Cancel</AlertDialogCancel>
											<AlertDialogAction className="bg-destructive text-destructive-foreground hover:bg-destructive/90" onClick={() => router.delete(`/admin/users/${user.id}/`)}>
												Delete
											</AlertDialogAction>
										</AlertDialogFooter>
									</AlertDialogContent>
								</AlertDialog>
							</CardContent>
						</Card>
					</div>
				</div>
			</Container>
		</>
	)
}

AdminUserDetail.layout = (page: React.ReactNode) => <AdminLayout>{page}</AdminLayout>
