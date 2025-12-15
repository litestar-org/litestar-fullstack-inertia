import { Head } from "@inertiajs/react"
import type React from "react"
import { Container } from "@/components/container"
import { Header } from "@/components/header"
import { AppLayout } from "@/layouts/app-layout"

export default function TeamList({ about: _about }: { about: string }) {
	return (
		<>
			<Head title="Teams" />
			<Header title="All Teams" />
			<Container>
				{/* Your about page content goes here. */}
				<div className="text-lime-600 dark:text-lime-400">"resources/pages/team/list.tsx"</div>
			</Container>
		</>
	)
}

TeamList.layout = (page: React.ReactNode) => <AppLayout>{page}</AppLayout>
