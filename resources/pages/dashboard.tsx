import { Head, usePage } from "@inertiajs/react"
import { Container } from "@/components/container"
import { Header } from "@/components/header"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { AppLayout } from "@/layouts/app-layout"

export default function Dashboard() {
	const { auth } = usePage<InertiaProps>().props
	return (
		<>
			<Head title="Dashboard" />
			<Header title="Dashboard" />
			<Container>
				<Card>
					<CardHeader>
						<CardTitle>Welcome</CardTitle>
					</CardHeader>
					<CardContent>
						Hi {auth?.user?.name}, you are now logged in.
						<div className="mb-2 flex text-muted-foreground">
							This python content of this page is rendered from the <span className="flex text-lime-600 dark:text-lime-400">`WebController`</span>
							class in <span className="text-lime-600 dark:text-lime-400"> `app/domain/web/controller.py`</span>
						</div>
						<div className="mb-2 flex text-muted-foreground">
							The React component is loaded by the <div className="text-lime-600 dark:text-lime-400">`component`</div> prop and points to
							<div className="text-lime-600 dark:text-lime-400">"resources/pages/dashboard.tsx"</div>
						</div>
					</CardContent>
				</Card>
				<Card className="mt-10">
					<CardHeader>
						<CardTitle>Inertia Features</CardTitle>
					</CardHeader>
					<CardContent>
						<div className="flex">
							This app makes use of the InertiaJS integration <div className="text-lime-600 dark:text-lime-400">`litestar-vite`</div>.
						</div>
					</CardContent>
				</Card>
			</Container>
		</>
	)
}

Dashboard.layout = (page: any) => <AppLayout>{page}</AppLayout>
