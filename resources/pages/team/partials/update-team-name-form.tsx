import { useForm } from "@inertiajs/react"
import { InputError } from "@/components/input-error"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { toast } from "@/components/ui/use-toast"
import type { TeamDetail } from "@/lib/generated/api/types.gen"
import { route } from "@/lib/generated/routes"

interface Props {
	team: Pick<TeamDetail, "id" | "name" | "slug">
}

export default function UpdateTeamNameForm({ team }: Props) {
	const { data, setData, patch, processing, errors } = useForm({
		name: team.name,
	})

	const submit = (e: React.FormEvent) => {
		e.preventDefault()
		patch(route("teams.edit", { team_slug: team.slug }), {
			preserveScroll: true,
			onSuccess: () => {
				toast({ description: "Team name updated." })
			},
		})
	}

	return (
		<Card>
			<CardHeader>
				<CardTitle>Team Name</CardTitle>
				<CardDescription>The team's name and owner information.</CardDescription>
			</CardHeader>
			<CardContent>
				<form onSubmit={submit} className="space-y-6">
					<div>
						<Label htmlFor="name">Team Name</Label>
						<Input id="name" value={data.name} onChange={(e) => setData("name", e.target.value)} className="mt-1" required />
						<InputError message={errors.name} className="mt-2" />
					</div>

					<Button type="submit" disabled={processing}>
						Save
					</Button>
				</form>
			</CardContent>
		</Card>
	)
}
