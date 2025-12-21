import { Head, Link } from "@inertiajs/react"
import { Plus, Users } from "lucide-react"
import type React from "react"
import { Container } from "@/components/container"
import { Header } from "@/components/header"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { AppLayout } from "@/layouts/app-layout"
import type { PagePropsFor } from "@/lib/generated/page-props"
import { route } from "@/lib/generated/routes"
import { cn } from "@/lib/utils"

const roleStyles: Record<string, string> = {
	owner: "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200",
	admin: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
	member: "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200",
}

export default function TeamList({ teams }: PagePropsFor<"team/list">) {
	return (
		<>
			<Head title="Teams" />
			<Header title="Teams">
				<Link href={route("teams.create")}>
					<Button>
						<Plus className="mr-2 h-4 w-4" />
						Create Team
					</Button>
				</Link>
			</Header>
			<Container>
				{teams.length === 0 ? (
					<Card>
						<CardContent className="flex flex-col items-center justify-center py-12">
							<Users className="h-12 w-12 text-muted-foreground" />
							<h3 className="mt-4 font-semibold text-lg">No teams yet</h3>
							<p className="mt-2 text-muted-foreground text-sm">Create your first team to start collaborating.</p>
							<Link href={route("teams.create")} className="mt-4">
								<Button>
									<Plus className="mr-2 h-4 w-4" />
									Create Team
								</Button>
							</Link>
						</CardContent>
					</Card>
				) : (
					<div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
						{teams.map((team) => (
							<Link key={team.id} href={route("teams.show", { team_slug: team.slug })}>
								<Card className="transition-shadow hover:shadow-md">
									<CardHeader>
										<div className="flex items-start justify-between">
											<CardTitle className="text-lg">{team.name}</CardTitle>
											<Badge className={cn("capitalize", roleStyles[team.userRole])}>{team.userRole}</Badge>
										</div>
										{team.description && <CardDescription className="line-clamp-2">{team.description}</CardDescription>}
									</CardHeader>
									<CardContent>
										<div className="flex items-center text-muted-foreground text-sm">
											<Users className="mr-1 h-4 w-4" />
											{team.memberCount} {team.memberCount === 1 ? "member" : "members"}
										</div>
									</CardContent>
								</Card>
							</Link>
						))}
					</div>
				)}
			</Container>
		</>
	)
}

TeamList.layout = (page: React.ReactNode) => <AppLayout>{page}</AppLayout>
