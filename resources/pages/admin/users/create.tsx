import { Head, Link, useForm } from "@inertiajs/react"
import { ArrowLeft } from "lucide-react"
import { Container } from "@/components/container"
import { Header } from "@/components/header"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { AdminLayout } from "@/layouts/admin-layout"

interface RoleOption {
	id: string
	slug: string
	name: string
}

interface Props {
	availableRoles: RoleOption[]
}

export default function AdminUserCreate({ availableRoles }: Props) {
	const { data, setData, post, processing, errors } = useForm({
		email: "",
		password: "",
		name: "",
		isSuperuser: false,
		isActive: true,
		isVerified: false,
	})

	const handleSubmit = (e: React.FormEvent) => {
		e.preventDefault()
		post("/admin/users/")
	}

	return (
		<>
			<Head title="Create User - Admin" />
			<Header title="Create User">
				<Link href="/admin/users">
					<Button variant="outline">
						<ArrowLeft className="mr-2 h-4 w-4" />
						Back to Users
					</Button>
				</Link>
			</Header>
			<Container>
				<div className="mx-auto max-w-2xl">
					<Card>
						<CardHeader>
							<CardTitle>New User</CardTitle>
							<CardDescription>Create a new user account</CardDescription>
						</CardHeader>
						<CardContent>
							<form onSubmit={handleSubmit} className="space-y-4">
								<div className="space-y-2">
									<Label htmlFor="email">Email *</Label>
									<Input id="email" type="email" value={data.email} onChange={(e) => setData("email", e.target.value)} placeholder="user@example.com" required />
									{errors.email && <p className="text-destructive text-sm">{errors.email}</p>}
								</div>

								<div className="space-y-2">
									<Label htmlFor="password">Password *</Label>
									<Input id="password" type="password" value={data.password} onChange={(e) => setData("password", e.target.value)} placeholder="Enter a strong password" required />
									{errors.password && <p className="text-destructive text-sm">{errors.password}</p>}
								</div>

								<div className="space-y-2">
									<Label htmlFor="name">Name</Label>
									<Input id="name" value={data.name} onChange={(e) => setData("name", e.target.value)} placeholder="John Doe" />
									{errors.name && <p className="text-destructive text-sm">{errors.name}</p>}
								</div>

								<div className="space-y-4 rounded-lg border p-4">
									<div className="flex items-center justify-between">
										<div>
											<Label htmlFor="isActive">Active</Label>
											<p className="text-muted-foreground text-sm">User can log in</p>
										</div>
										<Switch id="isActive" checked={data.isActive} onCheckedChange={(checked) => setData("isActive", checked)} />
									</div>

									<div className="flex items-center justify-between">
										<div>
											<Label htmlFor="isVerified">Verified</Label>
											<p className="text-muted-foreground text-sm">Email is verified</p>
										</div>
										<Switch id="isVerified" checked={data.isVerified} onCheckedChange={(checked) => setData("isVerified", checked)} />
									</div>

									<div className="flex items-center justify-between">
										<div>
											<Label htmlFor="isSuperuser">Superuser</Label>
											<p className="text-muted-foreground text-sm">Full admin access</p>
										</div>
										<Switch id="isSuperuser" checked={data.isSuperuser} onCheckedChange={(checked) => setData("isSuperuser", checked)} />
									</div>
								</div>

								<div className="flex gap-2 pt-4">
									<Button type="submit" disabled={processing}>
										{processing ? "Creating..." : "Create User"}
									</Button>
									<Link href="/admin/users">
										<Button variant="outline" type="button">
											Cancel
										</Button>
									</Link>
								</div>
							</form>
						</CardContent>
					</Card>
				</div>
			</Container>
		</>
	)
}

AdminUserCreate.layout = (page: React.ReactNode) => <AdminLayout>{page}</AdminLayout>
