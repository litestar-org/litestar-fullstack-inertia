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

export default function ConfirmPassword() {
	const { data, setData, post, processing, errors, reset } = useForm({
		password: "",
	})

	useEffect(() => {
		return () => {
			reset("password")
		}
	}, [reset])

	const submit = (e: React.FormEvent) => {
		e.preventDefault()
		post(route("password.confirm"))
	}

	return (
		<>
			<Head title="Confirm Password" />

			<AuthHeroPanel title="Litestar Fullstack" description="Security verification required. Your account is protected." />

			<div className="flex flex-col justify-center px-4 py-8 sm:px-6 lg:px-8">
				<div className="mx-auto flex w-full flex-col justify-center space-y-6 sm:w-87.5">
					<div className="flex flex-col space-y-2 text-center">
						<h1 className="flex items-center justify-center gap-2 font-semibold text-2xl tracking-tight">
							<Icons.lock className="h-5 w-5" />
							Confirm Password
						</h1>
						<p className="text-muted-foreground text-sm">This is a secure area. Please confirm your password before continuing.</p>
					</div>

					<form onSubmit={submit} className="space-y-4">
						<div>
							<Label htmlFor="password">Password</Label>
							<Input
								id="password"
								type="password"
								name="password"
								value={data.password}
								className="mt-1"
								autoFocus
								autoComplete="current-password"
								onChange={(e) => setData("password", e.target.value)}
							/>
							<InputError message={errors.password} className="mt-2" />
						</div>

						<Button type="submit" className="w-full" disabled={processing}>
							Confirm
						</Button>
					</form>
				</div>
			</div>
		</>
	)
}

ConfirmPassword.layout = (page: React.ReactNode) => <GuestLayout>{page}</GuestLayout>
