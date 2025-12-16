import { useForm } from "@inertiajs/react"
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
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { route } from "@/lib/generated/routes"

interface Team {
	id: string
	name: string
}

interface Props {
	team: Team
}

export default function DeleteTeamForm({ team }: Props) {
	const { delete: destroy, processing } = useForm()

	const deleteTeam = () => {
		destroy(route("teams.remove", { team_id: team.id }))
	}

	return (
		<Card className="border-destructive">
			<CardHeader>
				<CardTitle>Delete Team</CardTitle>
				<CardDescription>Permanently delete this team and all of its data.</CardDescription>
			</CardHeader>
			<CardContent>
				<p className="mb-4 text-muted-foreground text-sm">
					Once a team is deleted, all of its resources and data will be permanently deleted. Before deleting this team, please download any data or information regarding this team
					that you wish to retain.
				</p>

				<AlertDialog>
					<AlertDialogTrigger asChild>
						<Button variant="destructive">Delete Team</Button>
					</AlertDialogTrigger>
					<AlertDialogContent>
						<AlertDialogHeader>
							<AlertDialogTitle>Delete {team.name}?</AlertDialogTitle>
							<AlertDialogDescription>
								Are you sure you want to delete this team? This action cannot be undone. All team members will lose access and all team data will be permanently removed.
							</AlertDialogDescription>
						</AlertDialogHeader>
						<AlertDialogFooter>
							<AlertDialogCancel>Cancel</AlertDialogCancel>
							<AlertDialogAction onClick={deleteTeam} disabled={processing} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
								Delete Team
							</AlertDialogAction>
						</AlertDialogFooter>
					</AlertDialogContent>
				</AlertDialog>
			</CardContent>
		</Card>
	)
}
