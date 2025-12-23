import { Head, Link, router, useForm } from "@inertiajs/react"
import { format } from "date-fns"
import { ArrowLeft, Trash2, UserMinus } from "lucide-react"
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
import { Separator } from "@/components/ui/separator"
import { Switch } from "@/components/ui/switch"
import { Textarea } from "@/components/ui/textarea"
import { useToast } from "@/components/ui/use-toast"
import { AdminLayout } from "@/layouts/admin-layout"
import { getGravatarUrl, getInitials } from "@/lib/utils"

interface TeamMemberInfo {
	id: string
	userId: string
	email: string
	name: string | null
	role: string
	isOwner: boolean
	avatarUrl: string | null
}

interface AdminTeamDetail {
	id: string
	name: string
	slug: string
	description: string | null
	isActive: boolean
	members: TeamMemberInfo[]
	createdAt: string | null
	updatedAt: string | null
}

interface Props {
	team: AdminTeamDetail
}

const roleStyles: Record<string, string> = {
	owner: "bg-[#EDB641] text-[#202235]",
	admin: "bg-[#202235] text-white",
	editor: "bg-[#FFD480] text-[#202235]",
	member: "bg-[#DCDFE4] text-[#202235]",
}

export default function AdminTeamDetail({ team }: Props) {
	const { toast } = useToast()

	const { data, setData, patch, processing } = useForm({
		name: team.name,
		description: team.description || "",
		isActive: team.isActive,
	})

	const handleSubmit = (e: React.FormEvent) => {
		e.preventDefault()
		patch(`/admin/teams/${team.id}/`, {
			preserveScroll: true,
			onSuccess: () => {
				toast({ description: "Team updated successfully.", variant: "success" })
			},
		})
	}

	const handleRemoveMember = (memberId: string) => {
		router.delete(`/admin/teams/${team.id}/members/${memberId}/`, {
			preserveScroll: true,
			onSuccess: () => {
				toast({ description: "Member removed successfully.", variant: "success" })
			},
		})
	}

	return (
		<>
			<Head title={`${team.name} - Admin`} />
			<Header title={team.name}>
				<Link href="/admin/teams">
					<Button variant="outline">
						<ArrowLeft className="mr-2 h-4 w-4" />
						Back to Teams
					</Button>
				</Link>
			</Header>
			<Container>
				<div className="grid gap-6 lg:grid-cols-3">
					{/* Team Info */}
					<div className="lg:col-span-2">
						<Card>
							<CardHeader>
								<CardTitle>Team Details</CardTitle>
								<CardDescription>Update team information</CardDescription>
							</CardHeader>
							<CardContent>
								<form onSubmit={handleSubmit} className="space-y-4">
									<div className="space-y-2">
										<Label htmlFor="name">Name</Label>
										<Input id="name" value={data.name} onChange={(e) => setData("name", e.target.value)} />
									</div>

									<div className="space-y-2">
										<Label htmlFor="description">Description</Label>
										<Textarea id="description" value={data.description} onChange={(e) => setData("description", e.target.value)} rows={3} />
									</div>

									<div className="flex items-center space-x-2">
										<Switch id="isActive" checked={data.isActive} onCheckedChange={(checked) => setData("isActive", checked)} />
										<Label htmlFor="isActive">Active</Label>
									</div>

									<Button type="submit" disabled={processing}>
										{processing ? "Saving..." : "Save Changes"}
									</Button>
								</form>
							</CardContent>
						</Card>

						{/* Members */}
						<Card className="mt-6">
							<CardHeader>
								<CardTitle>Members ({team.members.length})</CardTitle>
								<CardDescription>Team member management</CardDescription>
							</CardHeader>
							<CardContent>
								{team.members.length > 0 ? (
									<div className="space-y-3">
										{team.members.map((member) => (
											<div key={member.id} className="flex items-center justify-between rounded-md border p-3">
												<div className="flex items-center gap-3">
													<Avatar className="h-10 w-10">
														<AvatarImage src={member.avatarUrl ?? getGravatarUrl(member.email)} />
														<AvatarFallback>{getInitials(member.email)}</AvatarFallback>
													</Avatar>
													<div>
														<p className="font-medium">{member.name || member.email}</p>
														{member.name && <p className="text-muted-foreground text-sm">{member.email}</p>}
													</div>
												</div>
												<div className="flex items-center gap-2">
													<Badge className={roleStyles[member.isOwner ? "owner" : member.role] || roleStyles.member}>{member.isOwner ? "Owner" : member.role}</Badge>
													{!member.isOwner && (
														<AlertDialog>
															<AlertDialogTrigger asChild>
																<Button variant="ghost" size="icon">
																	<UserMinus className="h-4 w-4" />
																</Button>
															</AlertDialogTrigger>
															<AlertDialogContent>
																<AlertDialogHeader>
																	<AlertDialogTitle>Remove Member</AlertDialogTitle>
																	<AlertDialogDescription>Are you sure you want to remove {member.email} from this team?</AlertDialogDescription>
																</AlertDialogHeader>
																<AlertDialogFooter>
																	<AlertDialogCancel>Cancel</AlertDialogCancel>
																	<AlertDialogAction onClick={() => handleRemoveMember(member.id)}>Remove</AlertDialogAction>
																</AlertDialogFooter>
															</AlertDialogContent>
														</AlertDialog>
													)}
												</div>
											</div>
										))}
									</div>
								) : (
									<p className="text-muted-foreground">No members</p>
								)}
							</CardContent>
						</Card>
					</div>

					{/* Sidebar */}
					<div className="space-y-6">
						{/* Status */}
						<Card>
							<CardHeader>
								<CardTitle>Information</CardTitle>
							</CardHeader>
							<CardContent className="space-y-4">
								<div>
									<p className="text-muted-foreground text-sm">Slug</p>
									<p className="font-mono text-sm">{team.slug}</p>
								</div>

								<div>
									<p className="text-muted-foreground text-sm">Status</p>
									{team.isActive ? (
										<Badge variant="outline" className="border-green-500 text-green-600">
											Active
										</Badge>
									) : (
										<Badge variant="destructive">Inactive</Badge>
									)}
								</div>

								<Separator />

								<div className="space-y-2 text-sm">
									<p>
										<span className="text-muted-foreground">Created:</span> {team.createdAt ? format(new Date(team.createdAt), "MMM d, yyyy 'at' h:mm a") : "-"}
									</p>
									<p>
										<span className="text-muted-foreground">Updated:</span> {team.updatedAt ? format(new Date(team.updatedAt), "MMM d, yyyy 'at' h:mm a") : "-"}
									</p>
								</div>
							</CardContent>
						</Card>

						{/* Danger Zone */}
						<Card className="border-destructive">
							<CardHeader>
								<CardTitle className="text-destructive">Danger Zone</CardTitle>
							</CardHeader>
							<CardContent>
								<AlertDialog>
									<AlertDialogTrigger asChild>
										<Button variant="destructive" className="w-full">
											<Trash2 className="mr-2 h-4 w-4" />
											Delete Team
										</Button>
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
							</CardContent>
						</Card>
					</div>
				</div>
			</Container>
		</>
	)
}

AdminTeamDetail.layout = (page: React.ReactNode) => <AdminLayout>{page}</AdminLayout>
