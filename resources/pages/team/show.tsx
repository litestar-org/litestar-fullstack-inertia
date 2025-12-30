import { Head, Link } from "@inertiajs/react"
import { formatDistanceToNow } from "date-fns"
import type { LucideIcon } from "lucide-react"
import { Calendar, Clock, Mail, Settings, Shield, ShieldCheck, Tag, Users } from "lucide-react"
import type React from "react"
import { Container } from "@/components/container"
import { Header } from "@/components/header"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet"
import { AppLayout } from "@/layouts/app-layout"
import type { PagePropsFor } from "@/lib/generated/page-props"
import { route } from "@/lib/generated/routes"
import { cn, getGravatarUrl, getInitials } from "@/lib/utils"
import TeamMemberManager from "@/pages/team/partials/team-member-manager"

const roleStyles: Record<string, string> = {
	owner: "bg-[#EDB641] text-[#202235] dark:bg-[#EDB641] dark:text-[#202235]",
	admin: "bg-[#202235] text-white dark:bg-[#202235] dark:text-white",
	editor: "bg-[#FFD480] text-[#202235] dark:bg-[#FFD480] dark:text-[#202235]",
	member: "bg-[#DCDFE4] text-[#202235] dark:bg-[#2A2D45] dark:text-white",
}

const roleIcons: Record<string, LucideIcon | null> = {
	owner: ShieldCheck,
	admin: Shield,
	editor: Shield,
	member: null,
}

export default function TeamShow({ team, members, permissions, pendingInvitations = [] }: PagePropsFor<"team/show">) {
	const canManageTeam = permissions.canUpdateTeam || permissions.canDeleteTeam

	return (
		<>
			<Head title={team.name} />
			<Header title={team.name}>
				{canManageTeam && (
					<Link href={route("teams.settings", { team_slug: team.slug })}>
						<Button variant="outline" size="sm">
							<Settings className="mr-2 h-4 w-4" />
							Team Settings
						</Button>
					</Link>
				)}
			</Header>
			<Container>
				<div className="grid gap-6 lg:grid-cols-3">
					{/* Team Overview */}
					<div className="lg:col-span-2 space-y-6">
						<Card>
							<CardHeader>
								<CardTitle>About</CardTitle>
							</CardHeader>
							<CardContent>
								{team.description ? <p className="text-muted-foreground">{team.description}</p> : <p className="text-muted-foreground italic">No description provided.</p>}
								{/* Tags */}
								{team.tags && team.tags.length > 0 && (
									<div className="mt-4 flex flex-wrap gap-2">
										{team.tags.map((tag) => (
											<Badge key={tag.id} variant="secondary" className="flex items-center gap-1">
												<Tag className="h-3 w-3" />
												{tag.name}
											</Badge>
										))}
									</div>
								)}
								<div className="mt-4 flex flex-wrap gap-4 text-sm text-muted-foreground">
									<div className="flex items-center">
										<Users className="mr-2 h-4 w-4" />
										{members.length} {members.length === 1 ? "member" : "members"}
									</div>
									{team.createdAt && (
										<div className="flex items-center">
											<Calendar className="mr-2 h-4 w-4" />
											Created {new Date(team.createdAt).toLocaleDateString()}
										</div>
									)}
								</div>
							</CardContent>
						</Card>

						{/* Members List */}
						<Card>
							<CardHeader>
								<div className="flex items-center justify-between">
									<div>
										<CardTitle>Team Members</CardTitle>
										<CardDescription>People who are part of this team.</CardDescription>
									</div>
									{canManageTeam && (
										<Sheet>
											<SheetTrigger asChild>
												<Button variant="outline" size="sm">
													Manage Members
												</Button>
											</SheetTrigger>
											<SheetContent className="sm:max-w-xl overflow-y-auto">
												<SheetHeader>
													<SheetTitle>Manage Team Members</SheetTitle>
													<SheetDescription>Add or remove members from {team.name}.</SheetDescription>
												</SheetHeader>
												<div className="mt-6">
													<TeamMemberManager team={team} members={members} permissions={permissions} />
												</div>
											</SheetContent>
										</Sheet>
									)}
								</div>
							</CardHeader>
							<CardContent>
								<div className="space-y-4">
									{members.map((member) => {
										const RoleIcon = roleIcons[member.role]
										return (
											<div key={member.id} className="flex items-center justify-between rounded-lg border p-4">
												<div className="flex items-center gap-4">
													<Avatar>
														<AvatarImage src={member.avatarUrl ?? getGravatarUrl(member.email)} />
														<AvatarFallback>{getInitials(member.name || member.email)}</AvatarFallback>
													</Avatar>
													<div>
														<div className="flex items-center gap-2">
															<span className="font-medium">{member.name || member.email}</span>
															<Badge className={cn("capitalize", roleStyles[member.role])}>
																{RoleIcon && <RoleIcon className="mr-1 h-3 w-3" />}
																{member.role}
															</Badge>
														</div>
														{member.name && <p className="text-muted-foreground text-sm">{member.email}</p>}
													</div>
												</div>
											</div>
										)
									})}
								</div>
							</CardContent>
						</Card>

						{/* Pending Invitations (read-only) */}
						{permissions.canAddTeamMembers && pendingInvitations.length > 0 && (
							<Card>
								<CardHeader>
									<div className="flex items-center justify-between">
										<div>
											<CardTitle>Pending Invitations</CardTitle>
											<CardDescription>
												{pendingInvitations.length} pending invitation{pendingInvitations.length !== 1 ? "s" : ""}
											</CardDescription>
										</div>
										<Link href={route("teams.settings", { team_slug: team.slug })}>
											<Button variant="outline" size="sm">
												Manage Invitations
											</Button>
										</Link>
									</div>
								</CardHeader>
								<CardContent>
									<div className="space-y-3">
										{pendingInvitations.map((invitation) => (
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
											</div>
										))}
									</div>
								</CardContent>
							</Card>
						)}
					</div>

					{/* Sidebar */}
					<div className="space-y-6">
						<Card>
							<CardHeader>
								<CardTitle>Quick Actions</CardTitle>
							</CardHeader>
							<CardContent className="space-y-2">
								{canManageTeam && (
									<Link href={route("teams.settings", { team_slug: team.slug })} className="block">
										<Button variant="outline" className="w-full justify-start">
											<Settings className="mr-2 h-4 w-4" />
											Team Settings
										</Button>
									</Link>
								)}
								<Link href={route("teams.list")} className="block">
									<Button variant="ghost" className="w-full justify-start">
										<Users className="mr-2 h-4 w-4" />
										View All Teams
									</Button>
								</Link>
							</CardContent>
						</Card>
					</div>
				</div>
			</Container>
		</>
	)
}

TeamShow.layout = (page: React.ReactNode) => <AppLayout>{page}</AppLayout>
