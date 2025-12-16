import { Head } from "@inertiajs/react"
import type React from "react"
import { Container } from "@/components/container"
import { Header } from "@/components/header"
import { AppLayout } from "@/layouts/app-layout"
import DeleteTeamForm from "@/pages/team/partials/delete-team-form"
import TeamMemberManager from "@/pages/team/partials/team-member-manager"
import UpdateTeamNameForm from "@/pages/team/partials/update-team-name-form"

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
	description: string | null
	slug: string
}

interface Permissions {
	canAddTeamMembers: boolean
	canDeleteTeam: boolean
	canRemoveTeamMembers: boolean
	canUpdateTeam: boolean
}

interface Props {
	team: Team
	members: TeamMember[]
	permissions: Permissions
}

export default function TeamShow({ team, members, permissions }: Props) {
	return (
		<>
			<Head title={team.name} />
			<Header title={team.name} />
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

TeamShow.layout = (page: React.ReactNode) => <AppLayout>{page}</AppLayout>
