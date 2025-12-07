import { Head, Link } from "@inertiajs/react"
import { Icons } from "@/components/icons"
import { buttonVariants } from "@/components/ui/button"
import { GuestLayout } from "@/layouts/guest-layout"
import { cn } from "@/lib/utils"
import UserRegistrationForm from "./partials/user-registration-form"

export default function Login() {
	return (
		<>
			<Head title="Register account" />
			<Link href={route("login")} className={cn(buttonVariants({ variant: "ghost" }), "absolute top-4 right-4 md:top-8 md:right-8")}>
				Already have an account?
			</Link>
			<div className="relative hidden h-full flex-col p-10 lg:flex dark:border-r">
				<div className="absolute inset-0 bg-none" />
				<Link href={route("home")}>
					<div className="relative z-20 flex items-center font-medium text-lg">
						<Icons.logo className="mr-2 h-6 w-6" />
						Litestar Fullstack Application
					</div>
				</Link>
				<div className="relative z-20 mt-auto" />
			</div>

			<div className="sm:pt-5 lg:p-8">
				<div className="mx-auto flex w-full flex-col justify-center space-y-6 sm:w-[350px]">
					<div className="flex flex-col space-y-2 text-center">
						<h1 className="mx-auto flex font-semibold text-2xl tracking-tight">
							<Icons.sparkle className="mr-3 h-5 w-5 " /> Signup to get started{" "}
						</h1>
						<p className="text-muted-foreground text-sm ">Create an account to continue.</p>
					</div>
					<UserRegistrationForm />
					<p className="px-8 text-center text-muted-foreground text-sm">
						By clicking continue, you agree to our{" "}
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
