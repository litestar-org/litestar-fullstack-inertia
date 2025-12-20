import { Head, Link } from "@inertiajs/react"
import type { LucideIcon } from "lucide-react"
import { Calendar, Settings, Shield, ShieldCheck, Users } from "lucide-react"
import type React from "react"
import { Container } from "@/components/container"
import { Header } from "@/components/header"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet"
import { AppLayout } from "@/layouts/app-layout"
import type { TeamDetailPage } from "@/lib/generated/api/types.gen"
import { route } from "@/lib/generated/routes"
import { cn, getGravatarUrl, getInitials } from "@/lib/utils"
import TeamMemberManager from "@/pages/team/partials/team-member-manager"

type Props = TeamDetailPage

const roleStyles: Record<string, string> = {
	owner: "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200",
	admin: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
	editor: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
	member: "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200",
}

const roleIcons: Record<string, LucideIcon | null> = {
	owner: ShieldCheck,
	admin: Shield,
	editor: Shield,
	member: null,
}

export default function TeamShow({ team, members, permissions }: Props) {
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
					</div>

					{/* Sidebar */}
					<div className="space-y-6">
						<Card>
							<CardHeader>
								<CardTitle>Quick Actions</CardTitle>
							</CardHeader>
							<CardContent className="space-y-2">
								{canManageTeam && (
									<Link href={route("teams.settings", { team_id: team.id })} className="block">
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
