import { Head, Link, useForm } from "@inertiajs/react"
import { AuthHeroPanel } from "@/components/auth-hero-panel"
import { Icons } from "@/components/icons"
import { InputError } from "@/components/input-error"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { GuestLayout } from "@/layouts/guest-layout"
import { route } from "@/lib/generated/routes"

interface ForgotPasswordProps {
	status: string
}

export default function ForgotPassword({ status }: ForgotPasswordProps) {
	const { data, setData, post, processing, errors } = useForm({
		email: "",
	})

	const submit = (e: React.FormEvent) => {
		e.preventDefault()
		post(route("password.email"))
	}

	return (
		<>
			<Head title="Forgot Password" />

			<AuthHeroPanel title="Litestar Fullstack" description="Secure password recovery for your account. We'll help you get back in." />

			<div className="flex flex-col justify-center px-4 py-8 sm:px-6 lg:px-8">
				<div className="mx-auto flex w-full flex-col justify-center space-y-6 sm:w-87.5">
					<div className="flex flex-col space-y-2 text-center">
						<h1 className="flex items-center justify-center gap-2 font-semibold text-2xl tracking-tight">
							<Icons.mail className="h-5 w-5" />
							Password Recovery
						</h1>
						<p className="text-muted-foreground text-sm">Enter your email and we'll send you a reset link.</p>
					</div>

					{status && <div className="rounded-md bg-green-50 p-3 text-center font-medium text-green-600 text-sm dark:bg-green-900/20">{status}</div>}

					<form onSubmit={submit} className="space-y-4">
						<div>
							<Label htmlFor="email">Email</Label>
							<Input id="email" type="email" name="email" value={data.email} className="mt-1" autoFocus autoComplete="email" onChange={(e) => setData("email", e.target.value)} />
							<InputError message={errors.email} className="mt-2" />
						</div>

						<Button type="submit" className="w-full" disabled={processing}>
							Send Reset Link
						</Button>
					</form>

					<div className="text-center">
						<Link href={route("login")} className="text-sm text-muted-foreground underline-offset-4 hover:text-primary hover:underline">
							Back to login
						</Link>
					</div>
				</div>
			</div>
		</>
	)
}

ForgotPassword.layout = (page: React.ReactNode) => <GuestLayout>{page}</GuestLayout>
