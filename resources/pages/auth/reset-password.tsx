import { Head, useForm } from "@inertiajs/react"
import { useEffect } from "react"
import { AuthHeroPanel } from "@/components/auth-hero-panel"
import { Icons } from "@/components/icons"
import { InputError } from "@/components/input-error"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { GuestLayout } from "@/layouts/guest-layout"
import { route } from "@/lib/generated/routes"

interface ResetPasswordProps {
	token: string
	email: string
}

export default function ResetPassword({ token, email }: ResetPasswordProps) {
	const { data, setData, post, processing, errors, reset } = useForm({
		token: token,
		email: email,
		password: "",
		password_confirmation: "",
	})

	useEffect(() => {
		return () => {
			reset("password", "password_confirmation")
		}
	}, [reset])

	const submit = (e: React.FormEvent) => {
		e.preventDefault()
		post(route("password.update"))
	}

	return (
		<>
			<Head title="Reset Password" />

			<AuthHeroPanel title="Litestar Fullstack" description="Create a new secure password for your account." />

			<div className="flex flex-col justify-center px-4 py-8 sm:px-6 lg:px-8">
				<div className="mx-auto flex w-full flex-col justify-center space-y-6 sm:w-87.5">
					<div className="flex flex-col space-y-2 text-center">
						<h1 className="flex items-center justify-center gap-2 font-semibold text-2xl tracking-tight">
							<Icons.key className="h-5 w-5" />
							Create New Password
						</h1>
						<p className="text-muted-foreground text-sm">Choose a strong password for your account.</p>
					</div>

					<form onSubmit={submit} className="space-y-4">
						<div>
							<Label htmlFor="email">Email</Label>
							<Input id="email" type="email" name="email" value={data.email} className="mt-1" autoComplete="username" onChange={(e) => setData("email", e.target.value)} />
							<InputError message={errors.email} className="mt-2" />
						</div>

						<div>
							<Label htmlFor="password">New Password</Label>
							<Input
								id="password"
								type="password"
								name="password"
								value={data.password}
								className="mt-1"
								autoFocus
								autoComplete="new-password"
								onChange={(e) => setData("password", e.target.value)}
							/>
							<InputError message={errors.password} className="mt-2" />
						</div>

						<div>
							<Label htmlFor="password_confirmation">Confirm Password</Label>
							<Input
								id="password_confirmation"
								type="password"
								name="password_confirmation"
								value={data.password_confirmation}
								className="mt-1"
								autoComplete="new-password"
								onChange={(e) => setData("password_confirmation", e.target.value)}
							/>
							<InputError message={errors.password_confirmation} className="mt-2" />
						</div>

						<Button type="submit" className="w-full" disabled={processing}>
							Reset Password
						</Button>
					</form>
				</div>
			</div>
		</>
	)
}

ResetPassword.layout = (page: React.ReactNode) => <GuestLayout>{page}</GuestLayout>
