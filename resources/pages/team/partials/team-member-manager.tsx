import { useForm } from "@inertiajs/react"
import { Shield, ShieldCheck, Trash2, UserPlus } from "lucide-react"
import { useState } from "react"
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
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { toast } from "@/components/ui/use-toast"
import { route } from "@/lib/generated/routes"
import { cn, getGravatarUrl, getInitials } from "@/lib/utils"

interface TeamMember {
	id: string
	userId: string
	name: string | null
	email: string
	avatarUrl: string | null
	role: "owner" | "admin" | "editor" | "member"
}

interface Team {
	id: string
	name: string
}

interface Permissions {
	canAddTeamMembers: boolean
	canRemoveTeamMembers: boolean
}

interface Props {
	team: Team
	members: TeamMember[]
	permissions: Permissions
}

const roleStyles = {
	owner: "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200",
	admin: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
	editor: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
	member: "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200",
}

const roleIcons = {
	owner: ShieldCheck,
	admin: Shield,
	editor: Shield,
	member: null,
}

export default function TeamMemberManager({ team, members, permissions }: Props) {
	const [showAddMemberDialog, setShowAddMemberDialog] = useState(false)
	const [memberToRemove, setMemberToRemove] = useState<TeamMember | null>(null)

	const addMemberForm = useForm({
		user_name: "",
	})

	const removeMemberForm = useForm({
		user_name: "",
	})

	const addMember = (e: React.FormEvent) => {
		e.preventDefault()
		addMemberForm.post(route("teams:add-member", { team_id: team.id }), {
			preserveScroll: true,
			onSuccess: () => {
				addMemberForm.reset()
				setShowAddMemberDialog(false)
				toast({ description: "Team member added." })
			},
		})
	}

	const removeMember = () => {
		if (!memberToRemove) return
		removeMemberForm.setData("user_name", memberToRemove.email)
		removeMemberForm.post(route("teams:remove-member", { team_id: team.id }), {
			preserveScroll: true,
			onSuccess: () => {
				setMemberToRemove(null)
				toast({ description: "Team member removed." })
			},
		})
	}

	return (
		<Card>
			<CardHeader>
				<div className="flex items-center justify-between">
					<div>
						<CardTitle>Team Members</CardTitle>
						<CardDescription>All of the people that are part of this team.</CardDescription>
					</div>
					{permissions.canAddTeamMembers && (
						<Dialog open={showAddMemberDialog} onOpenChange={setShowAddMemberDialog}>
							<DialogTrigger asChild>
								<Button size="sm">
									<UserPlus className="mr-2 h-4 w-4" />
									Add Member
								</Button>
							</DialogTrigger>
							<DialogContent>
								<form onSubmit={addMember}>
									<DialogHeader>
										<DialogTitle>Add Team Member</DialogTitle>
										<DialogDescription>Add a new team member by their email address. They must already have an account.</DialogDescription>
									</DialogHeader>
									<div className="my-4">
										<Label htmlFor="user_name">Email Address</Label>
										<Input
											id="user_name"
											type="email"
											value={addMemberForm.data.user_name}
											onChange={(e) => addMemberForm.setData("user_name", e.target.value)}
											className="mt-1"
											placeholder="member@example.com"
											autoFocus
										/>
										<InputError message={addMemberForm.errors.user_name} className="mt-2" />
									</div>
									<DialogFooter>
										<Button type="button" variant="outline" onClick={() => setShowAddMemberDialog(false)}>
											Cancel
										</Button>
										<Button type="submit" disabled={addMemberForm.processing}>
											Add Member
										</Button>
									</DialogFooter>
								</form>
							</DialogContent>
						</Dialog>
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
								{permissions.canRemoveTeamMembers && member.role !== "owner" && (
									<AlertDialog open={memberToRemove?.id === member.id} onOpenChange={(open) => !open && setMemberToRemove(null)}>
										<AlertDialogTrigger asChild>
											<Button variant="ghost" size="icon" className="text-muted-foreground hover:text-destructive" onClick={() => setMemberToRemove(member)}>
												<Trash2 className="h-4 w-4" />
											</Button>
										</AlertDialogTrigger>
										<AlertDialogContent>
											<AlertDialogHeader>
												<AlertDialogTitle>Remove Team Member</AlertDialogTitle>
												<AlertDialogDescription>
													Are you sure you want to remove {member.name || member.email} from {team.name}? They will lose access to all team resources.
												</AlertDialogDescription>
											</AlertDialogHeader>
											<AlertDialogFooter>
												<AlertDialogCancel>Cancel</AlertDialogCancel>
												<AlertDialogAction
													onClick={removeMember}
													disabled={removeMemberForm.processing}
													className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
												>
													Remove Member
												</AlertDialogAction>
											</AlertDialogFooter>
										</AlertDialogContent>
									</AlertDialog>
								)}
							</div>
						)
					})}
				</div>
			</CardContent>
		</Card>
	)
}
