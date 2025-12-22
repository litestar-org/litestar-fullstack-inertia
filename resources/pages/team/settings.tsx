import { Head, Link, useForm } from "@inertiajs/react"
import { formatDistanceToNow } from "date-fns"
import { ArrowLeft, Clock, Mail, Pencil, Send, Trash2, UserPlus, Users } from "lucide-react"
import type React from "react"
import { useState } from "react"
import { Container } from "@/components/container"
import { Header } from "@/components/header"
import { InputError } from "@/components/input-error"
import { SettingsSidebar, type SettingsSidebarItem } from "@/components/settings-sidebar"
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
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { toast } from "@/components/ui/use-toast"
import { AppLayout } from "@/layouts/app-layout"
import type { TeamDetailPage, TeamInvitationItem } from "@/lib/generated/api/types.gen"
import { route } from "@/lib/generated/routes"
import DeleteTeamForm from "@/pages/team/partials/delete-team-form"
import TeamMemberManager from "@/pages/team/partials/team-member-manager"
import UpdateTeamNameForm from "@/pages/team/partials/update-team-name-form"

type Props = TeamDetailPage
type PendingInvitation = TeamInvitationItem & { inviteeExists?: boolean }

const getSidebarItems = (permissions: Props["permissions"]): SettingsSidebarItem[] => {
	const items: SettingsSidebarItem[] = []

	if (permissions.canUpdateTeam) {
		items.push({
			id: "team-details",
			label: "Team Details",
			icon: Pencil,
			description: "Update team name and info",
		})
	}

	items.push({
		id: "team-members",
		label: "Team Members",
		icon: Users,
		description: "Manage team membership",
	})

	if (permissions.canAddTeamMembers) {
		items.push({
			id: "pending-invitations",
			label: "Invitations",
			icon: Mail,
			description: "Manage pending invites",
		})
	}

	if (permissions.canDeleteTeam) {
		items.push({
			id: "delete-team",
			label: "Delete Team",
			icon: Trash2,
			description: "Permanently delete this team",
		})
	}

	return items
}

export default function TeamSettings({ team, members, permissions, pendingInvitations = [] }: Props) {
	const invitations = pendingInvitations as PendingInvitation[]
	const sidebarItems = getSidebarItems(permissions)
	const [activeSection, setActiveSection] = useState(() => sidebarItems[0]?.id ?? "team-members")
	const [showInviteDialog, setShowInviteDialog] = useState(false)
	const [invitationToCancel, setInvitationToCancel] = useState<TeamInvitationItem | null>(null)

	const inviteForm = useForm({
		email: "",
		role: "member",
	})

	const cancelForm = useForm({})

	const sendInvitation = (e: React.FormEvent) => {
		e.preventDefault()
		inviteForm.post(route("teams.invite", { team_slug: team.slug }), {
			preserveScroll: true,
			onSuccess: () => {
				inviteForm.reset()
				setShowInviteDialog(false)
			},
		})
	}

	const cancelInvitation = () => {
		if (!invitationToCancel) return
		cancelForm.delete(route("teams.invitation.cancel", { team_slug: team.slug, invitation_id: invitationToCancel.id }), {
			preserveScroll: true,
			onSuccess: () => {
				setInvitationToCancel(null)
				toast({ description: "Invitation cancelled.", variant: "warning" })
			},
		})
	}

	return (
		<>
			<Head title={`${team.name} Settings`} />
			<Header title="Team Settings">
				<Link href={route("teams.show", { team_slug: team.slug })}>
					<Button variant="outline" size="sm">
						<ArrowLeft className="mr-2 h-4 w-4" />
						Back to Team
					</Button>
				</Link>
			</Header>
			<Container>
				<div className="grid gap-6 lg:grid-cols-3">
					{/* Main Content */}
					<div className="lg:col-span-2 space-y-6">
						{permissions.canUpdateTeam && (
							<div id="team-details">
								<UpdateTeamNameForm team={team} />
							</div>
						)}

						<div id="team-members">
							<TeamMemberManager team={team} members={members} permissions={permissions} />
						</div>

						{/* Pending Invitations Section */}
						{permissions.canAddTeamMembers && (
							<div id="pending-invitations">
								<Card>
									<CardHeader>
										<div className="flex items-center justify-between">
											<div>
												<CardTitle>Pending Invitations</CardTitle>
												<CardDescription>
													{pendingInvitations.length === 0 ? "No pending invitations" : `${invitations.length} pending invitation${invitations.length !== 1 ? "s" : ""}`}
												</CardDescription>
											</div>
											<Dialog open={showInviteDialog} onOpenChange={setShowInviteDialog}>
												<DialogTrigger asChild>
													<Button size="sm">
														<UserPlus className="mr-2 h-4 w-4" />
														Invite Member
													</Button>
												</DialogTrigger>
												<DialogContent>
													<form onSubmit={sendInvitation}>
														<DialogHeader>
															<DialogTitle>Invite Team Member</DialogTitle>
															<DialogDescription>Send an invitation email to add a new member to {team.name}.</DialogDescription>
														</DialogHeader>
														<div className="my-4 space-y-4">
															<div>
																<Label htmlFor="email">Email Address</Label>
																<Input
																	id="email"
																	type="email"
																	value={inviteForm.data.email}
																	onChange={(e) => inviteForm.setData("email", e.target.value)}
																	className="mt-1"
																	placeholder="member@example.com"
																	autoFocus
																/>
																<InputError message={inviteForm.errors.email} className="mt-2" />
															</div>
															<div>
																<Label htmlFor="role">Role</Label>
																<Select value={inviteForm.data.role} onValueChange={(value) => inviteForm.setData("role", value)}>
																	<SelectTrigger className="mt-1">
																		<SelectValue />
																	</SelectTrigger>
																	<SelectContent>
																		<SelectItem value="member">Member</SelectItem>
																		<SelectItem value="admin">Admin</SelectItem>
																	</SelectContent>
																</Select>
																<InputError message={inviteForm.errors.role} className="mt-2" />
															</div>
														</div>
														<DialogFooter>
															<Button type="button" variant="outline" onClick={() => setShowInviteDialog(false)}>
																Cancel
															</Button>
															<Button type="submit" disabled={inviteForm.processing}>
																<Send className="mr-2 h-4 w-4" />
																Send Invitation
															</Button>
														</DialogFooter>
													</form>
												</DialogContent>
											</Dialog>
										</div>
									</CardHeader>
									<CardContent>
										{invitations.length === 0 ? (
											<div className="flex flex-col items-center justify-center py-6 text-center">
												<Mail className="h-10 w-10 text-muted-foreground" />
												<p className="mt-3 text-muted-foreground text-sm">No pending invitations. Invite team members to start collaborating.</p>
											</div>
										) : (
											<div className="space-y-3">
												{invitations.map((invitation) => (
													<div key={invitation.id} className="flex items-center justify-between rounded-lg border p-3">
														<div className="flex items-center gap-3">
															<div className="flex h-9 w-9 items-center justify-center rounded-full bg-muted">
																<Mail className="h-4 w-4 text-muted-foreground" />
															</div>
															<div>
																<div className="flex items-center gap-2">
																	<span className="font-medium text-sm">{invitation.email}</span>
																	<Badge variant="secondary" className="text-xs capitalize">
																		{invitation.role}
																	</Badge>
																	<Badge variant="outline" className="text-xs">
																		{invitation.inviteeExists ? "Existing user" : "Invite to sign up"}
																	</Badge>
																	{invitation.isExpired && (
																		<Badge variant="destructive" className="text-xs">
																			Expired
																		</Badge>
																	)}
																</div>
																<div className="flex items-center gap-1 text-muted-foreground text-xs">
																	<Clock className="h-3 w-3" />
																	<span>Sent {formatDistanceToNow(new Date(invitation.createdAt), { addSuffix: true })}</span>
																</div>
															</div>
														</div>
														{permissions.canRemoveTeamMembers && (
															<AlertDialog open={invitationToCancel?.id === invitation.id} onOpenChange={(open) => !open && setInvitationToCancel(null)}>
																<AlertDialogTrigger asChild>
																	<Button
																		variant="ghost"
																		size="icon"
																		className="h-8 w-8 text-muted-foreground hover:text-destructive"
																		onClick={() => setInvitationToCancel(invitation)}
																	>
																		<Trash2 className="h-4 w-4" />
																	</Button>
																</AlertDialogTrigger>
																<AlertDialogContent>
																	<AlertDialogHeader>
																		<AlertDialogTitle>Cancel Invitation</AlertDialogTitle>
																		<AlertDialogDescription>
																			Are you sure you want to cancel the invitation to {invitation.email}? They will no longer be able to join the team with this link.
																		</AlertDialogDescription>
																	</AlertDialogHeader>
																	<AlertDialogFooter>
																		<AlertDialogCancel>Keep Invitation</AlertDialogCancel>
																		<AlertDialogAction
																			onClick={cancelInvitation}
																			disabled={cancelForm.processing}
																			className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
																		>
																			Cancel Invitation
																		</AlertDialogAction>
																	</AlertDialogFooter>
																</AlertDialogContent>
															</AlertDialog>
														)}
													</div>
												))}
											</div>
										)}
									</CardContent>
								</Card>
							</div>
						)}

						{permissions.canDeleteTeam && (
							<div id="delete-team">
								<DeleteTeamForm team={team} />
							</div>
						)}
					</div>

					{/* Sidebar */}
					<div className="space-y-6">
						<SettingsSidebar title="Settings" items={sidebarItems} activeId={activeSection} onItemClick={setActiveSection} />
					</div>
				</div>
			</Container>
		</>
	)
}

TeamSettings.layout = (page: React.ReactNode) => <AppLayout>{page}</AppLayout>
