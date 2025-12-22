import { Head, Link, useForm } from "@inertiajs/react"
import { formatDistanceToNow } from "date-fns"
import { ArrowLeft, Clock, Mail, Send, Trash2, UserPlus } from "lucide-react"
import type React from "react"
import { useState } from "react"
import { Container } from "@/components/container"
import { Header } from "@/components/header"
import { InputError } from "@/components/input-error"
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
import type { TeamInvitationItem, TeamInvitationsPage } from "@/lib/generated/api/types.gen"
import { route } from "@/lib/generated/routes"

type Props = TeamInvitationsPage
type PendingInvitation = TeamInvitationItem & { inviteeExists?: boolean }

export default function TeamInvitations({ team, invitations, permissions }: Props) {
	const pendingInvitations = invitations as PendingInvitation[]
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
			<Head title={`${team.name} - Invitations`} />
			<Header title="Team Invitations">
				<Link href={route("teams.settings", { team_slug: team.slug })}>
					<Button variant="outline" size="sm">
						<ArrowLeft className="mr-2 h-4 w-4" />
						Back to Settings
					</Button>
				</Link>
			</Header>
			<Container>
				<div className="max-w-3xl space-y-6">
					<Card>
						<CardHeader>
							<div className="flex items-center justify-between">
								<div>
									<CardTitle>Pending Invitations</CardTitle>
									<CardDescription>Manage pending invitations to {team.name}.</CardDescription>
								</div>
								{permissions.canAddTeamMembers && (
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
								)}
							</div>
						</CardHeader>
						<CardContent>
							{pendingInvitations.length === 0 ? (
								<div className="flex flex-col items-center justify-center py-8 text-center">
									<Mail className="h-12 w-12 text-muted-foreground" />
									<h3 className="mt-4 font-semibold text-lg">No pending invitations</h3>
									<p className="mt-2 text-muted-foreground text-sm">Invite team members to start collaborating.</p>
								</div>
							) : (
								<div className="space-y-4">
									{pendingInvitations.map((invitation) => (
										<div key={invitation.id} className="flex items-center justify-between rounded-lg border p-4">
											<div className="flex items-center gap-4">
												<div className="flex h-10 w-10 items-center justify-center rounded-full bg-muted">
													<Mail className="h-5 w-5 text-muted-foreground" />
												</div>
												<div>
													<div className="flex items-center gap-2">
														<span className="font-medium">{invitation.email}</span>
														<Badge variant="secondary" className="capitalize">
															{invitation.role}
														</Badge>
														<Badge variant="outline">{invitation.inviteeExists ? "Existing user" : "Invite to sign up"}</Badge>
														{invitation.isExpired && <Badge variant="destructive">Expired</Badge>}
													</div>
													<div className="flex items-center gap-2 text-muted-foreground text-sm">
														<Clock className="h-3 w-3" />
														<span>Sent {formatDistanceToNow(new Date(invitation.createdAt), { addSuffix: true })}</span>
														<span>by {invitation.invitedByEmail}</span>
													</div>
												</div>
											</div>
											{permissions.canRemoveTeamMembers && (
												<AlertDialog open={invitationToCancel?.id === invitation.id} onOpenChange={(open) => !open && setInvitationToCancel(null)}>
													<AlertDialogTrigger asChild>
														<Button variant="ghost" size="icon" className="text-muted-foreground hover:text-destructive" onClick={() => setInvitationToCancel(invitation)}>
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
			</Container>
		</>
	)
}

TeamInvitations.layout = (page: React.ReactNode) => <AppLayout>{page}</AppLayout>
