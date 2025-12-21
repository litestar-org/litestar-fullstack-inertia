import { Head, Link, usePage } from "@inertiajs/react"
import { AuthHeroPanel } from "@/components/auth-hero-panel"
import { Icons } from "@/components/icons"
import { buttonVariants } from "@/components/ui/button"
import { GuestLayout } from "@/layouts/guest-layout"
import type { PagePropsFor } from "@/lib/generated/page-props"
import { route } from "@/lib/generated/routes"
import { cn } from "@/lib/utils"
import UserLoginForm from "./partials/user-login-form"

export default function Login() {
	const { registrationEnabled } = usePage<PagePropsFor<"auth/login">>().props

	return (
		<>
			<Head title="Log in" />
			{registrationEnabled && (
				<Link href={route("register")} className={cn(buttonVariants({ variant: "ghost" }), "absolute top-4 right-4 md:top-8 md:right-8")}>
					Need an account?
				</Link>
			)}

			<AuthHeroPanel title="Litestar Fullstack" description="Build high-performance web applications with Python and React. Seamless SPA experience powered by Inertia.js." />

			<div className="flex flex-col justify-center px-4 py-8 sm:px-6 lg:px-8">
				<div className="mx-auto flex w-full flex-col justify-center space-y-6 sm:w-87.5">
					<div className="flex flex-col space-y-2 text-center">
						<h1 className="flex items-center justify-center gap-2 font-semibold text-2xl tracking-tight">
							<Icons.sparkle className="h-5 w-5" />
							Welcome back
						</h1>
						<p className="text-muted-foreground text-sm">Enter your credentials to sign in to your account</p>
					</div>

					<UserLoginForm />

					<div className="text-center">
						<Link href={route("forgot-password")} className="text-sm text-muted-foreground underline-offset-4 hover:text-primary hover:underline">
							Forgot your password?
						</Link>
					</div>

					<p className="px-8 text-center text-muted-foreground text-sm">
						By continuing, you agree to our{" "}
						<Link href={route("terms-of-service")} className="underline underline-offset-4 hover:text-primary">
							Terms of Service
						</Link>{" "}
						and{" "}
						<Link href={route("privacy-policy")} className="underline underline-offset-4 hover:text-primary">
							Privacy Policy
						</Link>
						.
					</p>
				</div>
			</div>
		</>
	)
}

Login.layout = (page: React.ReactNode) => {
	return <GuestLayout>{page}</GuestLayout>
}
