import { Head } from "@inertiajs/react"
import type React from "react"
import { Container } from "@/components/container"
import { Header } from "@/components/header"
import { AppLayout } from "@/layouts/app-layout"
import CreateTeamForm from "@/pages/team/partials/create-team-form"

export default function TeamCreate() {
	return (
		<>
			<Head title="Create Team" />
			<Header title="Create Team" />
			<Container>
				<div className="max-w-xl">
					<CreateTeamForm />
				</div>
			</Container>
		</>
	)
}

TeamCreate.layout = (page: React.ReactNode) => <AppLayout>{page}</AppLayout>
