import { Head, Link } from "@inertiajs/react"
import { ArrowLeft } from "lucide-react"
import type React from "react"
import { Container } from "@/components/container"
import { Header } from "@/components/header"
import { Button } from "@/components/ui/button"
import { AppLayout } from "@/layouts/app-layout"
import type { TeamDetailPage } from "@/lib/generated/api/types.gen"
import { route } from "@/lib/generated/routes"
import DeleteTeamForm from "@/pages/team/partials/delete-team-form"
import TeamMemberManager from "@/pages/team/partials/team-member-manager"
import UpdateTeamNameForm from "@/pages/team/partials/update-team-name-form"

type Props = TeamDetailPage

export default function TeamSettings({ team, members, permissions }: Props) {
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
				<div className="max-w-3xl space-y-6">
					{permissions.canUpdateTeam && <UpdateTeamNameForm team={team} />}

					<TeamMemberManager team={team} members={members} permissions={permissions} />

					{permissions.canDeleteTeam && <DeleteTeamForm team={team} />}
				</div>
			</Container>
		</>
	)
}

TeamSettings.layout = (page: React.ReactNode) => <AppLayout>{page}</AppLayout>
