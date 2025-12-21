import { router, useForm } from "@inertiajs/react"
import axios from "axios"
import type { LucideIcon } from "lucide-react"
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
import type { TeamDetail, TeamPageMember, TeamPermissions } from "@/lib/generated/api/types.gen"
import { route } from "@/lib/generated/routes"
import { cn, getGravatarUrl, getInitials } from "@/lib/utils"

interface Props {
	team: Pick<TeamDetail, "id" | "name" | "slug">
	members: TeamPageMember[]
	permissions: Pick<TeamPermissions, "canAddTeamMembers" | "canRemoveTeamMembers">
}

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

export default function TeamMemberManager({ team, members, permissions }: Props) {
	const [showAddMemberDialog, setShowAddMemberDialog] = useState(false)
	const [memberToRemove, setMemberToRemove] = useState<TeamPageMember | null>(null)
	const [isAdding, setIsAdding] = useState(false)
	const [isRemoving, setIsRemoving] = useState(false)

	const addMemberForm = useForm({
		userName: "",
	})

	const addMember = async (e: React.FormEvent) => {
		e.preventDefault()
		setIsAdding(true)
		addMemberForm.clearErrors()
		try {
			await axios.post(route("teams:add-member", { team_slug: team.slug }), {
				userName: addMemberForm.data.userName,
			})
			addMemberForm.reset()
			setShowAddMemberDialog(false)
			toast({ description: "Team member added." })
			router.reload()
		} catch (error) {
			if (axios.isAxiosError(error)) {
				const detail = error.response?.data?.detail
				const fieldErrors = error.response?.data?.errors
				if (detail) {
					addMemberForm.setError("userName", detail)
					return
				}
				if (fieldErrors?.userName) {
					addMemberForm.setError("userName", fieldErrors.userName)
					return
				}
			}
			toast({ description: "Failed to add team member. Please try again.", variant: "destructive" })
		} finally {
			setIsAdding(false)
		}
	}

	const removeMember = async () => {
		if (!memberToRemove) return
		setIsRemoving(true)
		try {
			await axios.post(route("teams:remove-member", { team_slug: team.slug }), {
				userName: memberToRemove.email,
			})
			setMemberToRemove(null)
			toast({ description: "Team member removed." })
			router.reload()
		} catch {
			toast({ description: "Failed to remove team member. Please try again.", variant: "destructive" })
		} finally {
			setIsRemoving(false)
		}
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
										<Label htmlFor="userName">Email Address</Label>
										<Input
											id="userName"
											type="email"
											value={addMemberForm.data.userName}
											onChange={(e) => addMemberForm.setData("userName", e.target.value)}
											className="mt-1"
											placeholder="member@example.com"
											autoFocus
											disabled={isAdding}
										/>
										<InputError message={addMemberForm.errors.userName} className="mt-2" />
									</div>
									<DialogFooter>
										<Button type="button" variant="outline" onClick={() => setShowAddMemberDialog(false)}>
											Cancel
										</Button>
										<Button type="submit" disabled={isAdding}>
											{isAdding ? "Adding..." : "Add Member"}
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
												<AlertDialogAction onClick={removeMember} disabled={isRemoving} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
													{isRemoving ? "Removing..." : "Remove Member"}
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
