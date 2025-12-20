import { Head, Link, useForm } from "@inertiajs/react"
import { AuthHeroPanel } from "@/components/auth-hero-panel"
import { Icons } from "@/components/icons"
import { Button } from "@/components/ui/button"
import { GuestLayout } from "@/layouts/guest-layout"
import { route } from "@/lib/generated/routes"

export default function VerifyEmail({ status }: { status?: string }) {
	const { post, processing } = useForm()

	const submit = (e: React.FormEvent) => {
		e.preventDefault()
		post(route("verification.send"))
	}

	return (
		<>
			<Head title="Email Verification" />

			<AuthHeroPanel title="Litestar Fullstack" description="Verify your email to unlock all features and secure your account." />

			<div className="flex flex-col justify-center px-4 py-8 sm:px-6 lg:px-8">
				<div className="mx-auto flex w-full flex-col justify-center space-y-6 sm:w-87.5">
					<div className="flex flex-col space-y-2 text-center">
						<h1 className="flex items-center justify-center gap-2 font-semibold text-2xl tracking-tight">
							<Icons.mailCheck className="h-5 w-5" />
							Verify Your Email
						</h1>
						<p className="text-muted-foreground text-sm">Thanks for signing up! Please verify your email address by clicking on the link we just sent you.</p>
					</div>

					{status === "verification-link-sent" && (
						<div className="rounded-md bg-green-50 p-3 text-center font-medium text-green-600 text-sm dark:bg-green-900/20">
							A new verification link has been sent to your email address.
						</div>
					)}

					<form onSubmit={submit} className="space-y-4">
						<Button type="submit" className="w-full" disabled={processing}>
							Resend Verification Email
						</Button>
					</form>

					<div className="text-center">
						<Link href={route("logout")} method="post" as="button" className="text-sm text-muted-foreground underline-offset-4 hover:text-primary hover:underline">
							Log Out
						</Link>
					</div>
				</div>
			</div>
		</>
	)
}

VerifyEmail.layout = (page: React.ReactNode) => <GuestLayout>{page}</GuestLayout>
