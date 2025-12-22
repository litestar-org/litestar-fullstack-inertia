import { Head, Link } from "@inertiajs/react"
import { formatDistanceToNow } from "date-fns"
import { Clock, Mail, Users } from "lucide-react"
import type React from "react"
import { Container } from "@/components/container"
import { Header } from "@/components/header"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { AppLayout } from "@/layouts/app-layout"
import type { UserPendingInvitationsPage } from "@/lib/generated/api/types.gen"
import { route } from "@/lib/generated/routes"

type Props = UserPendingInvitationsPage

export default function UserInvitations({ invitations }: Props) {
	return (
		<>
			<Head title="Pending Invitations" />
			<Header title="Pending Invitations" />
			<Container>
				<div className="max-w-3xl">
					<Card>
						<CardHeader>
							<CardTitle>Team Invitations</CardTitle>
							<CardDescription>You have been invited to join the following teams.</CardDescription>
						</CardHeader>
						<CardContent>
							{invitations.length === 0 ? (
								<div className="flex flex-col items-center justify-center py-8 text-center">
									<Mail className="h-12 w-12 text-muted-foreground" />
									<h3 className="mt-4 font-semibold text-lg">No pending invitations</h3>
									<p className="mt-2 text-muted-foreground text-sm">You don't have any pending team invitations.</p>
									<Link href={route("teams.list")} className="mt-4">
										<Button variant="outline">View Your Teams</Button>
									</Link>
								</div>
							) : (
								<div className="space-y-4">
									{invitations.map((invitation) => (
										<div key={invitation.id} className="flex items-center justify-between rounded-lg border p-4">
											<div className="flex items-center gap-4">
												<div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
													<Users className="h-6 w-6 text-primary" />
												</div>
												<div>
													<div className="flex items-center gap-2">
														<span className="font-medium">{invitation.teamName}</span>
														<Badge variant="secondary" className="capitalize">
															{invitation.role}
														</Badge>
													</div>
													<div className="flex items-center gap-2 text-muted-foreground text-sm">
														<span>Invited by {invitation.inviterName}</span>
														<span>-</span>
														<Clock className="h-3 w-3" />
														<span>{formatDistanceToNow(new Date(invitation.createdAt), { addSuffix: true })}</span>
													</div>
												</div>
											</div>
											<Link href={`/invitations/${invitation.id}/`}>
												<Button size="sm">View Invitation</Button>
											</Link>
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

UserInvitations.layout = (page: React.ReactNode) => <AppLayout>{page}</AppLayout>
