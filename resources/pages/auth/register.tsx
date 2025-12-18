import { Head, Link } from "@inertiajs/react"
import { AuthHeroPanel } from "@/components/auth-hero-panel"
import { Icons } from "@/components/icons"
import { buttonVariants } from "@/components/ui/button"
import { GuestLayout } from "@/layouts/guest-layout"
import { route } from "@/lib/generated/routes"
import { cn } from "@/lib/utils"
import UserRegistrationForm from "./partials/user-registration-form"

export default function Register() {
	return (
		<>
			<Head title="Create an account" />
			<Link href={route("login")} className={cn(buttonVariants({ variant: "ghost" }), "absolute top-4 right-4 md:top-8 md:right-8")}>
				Already have an account?
			</Link>

			<AuthHeroPanel title="Litestar Fullstack" description="Join thousands of developers building modern web applications with Python and React." />

			<div className="flex flex-col justify-center px-4 py-8 sm:px-6 lg:px-8">
				<div className="mx-auto flex w-full flex-col justify-center space-y-6 sm:w-87.5">
					<div className="flex flex-col space-y-2 text-center">
						<h1 className="flex items-center justify-center gap-2 font-semibold text-2xl tracking-tight">
							<Icons.sparkle className="h-5 w-5" />
							Create an account
						</h1>
						<p className="text-muted-foreground text-sm">Enter your details below to get started</p>
					</div>

					<UserRegistrationForm />

					<p className="px-8 text-center text-muted-foreground text-sm">
						By creating an account, you agree to our{" "}
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

Register.layout = (page: React.ReactNode) => {
	return <GuestLayout>{page}</GuestLayout>
}
