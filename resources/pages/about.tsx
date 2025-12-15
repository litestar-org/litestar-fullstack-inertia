import { Head } from "@inertiajs/react"
import type React from "react"
import { Container } from "@/components/container"
import { Header } from "@/components/header"
import { AppLayout } from "@/layouts/app-layout"

export default function About({ about: _about }: { about: string }) {
	return (
		<>
			<Head title="About Us" />
			<Header title="About Us" />
			<Container>
				{/* Your about page content goes here. */}
				<p>hello world</p>
			</Container>
		</>
	)
}

About.layout = (page: React.ReactNode) => <AppLayout>{page}</AppLayout>
