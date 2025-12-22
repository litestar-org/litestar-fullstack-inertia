import { Head, Link } from "@inertiajs/react"
import { ArrowLeftIcon } from "lucide-react"
import { AuthHeroPanel } from "@/components/auth-hero-panel"
import { buttonVariants } from "@/components/ui/button"
import { GuestLayout } from "@/layouts/guest-layout"
import Footer from "@/layouts/partials/footer"
import { route } from "@/lib/generated/routes"
import { cn } from "@/lib/utils"

interface Props {
	policy: string
}

export default function PrivacyPolicy({ policy }: Props) {
	return (
		<>
			<Head title="Privacy Policy" />

			<AuthHeroPanel title="Privacy & Security" description="Your privacy matters. Learn how we collect, use, and protect your personal information." showTestimonial={false} />

			<div className="flex h-full flex-col">
				{/* Fixed header */}
				<div className="sticky top-0 z-10 flex justify-end gap-2 border-b bg-background/95 p-4 backdrop-blur supports-backdrop-filter:bg-background/60 md:p-6">
					<Link href={route("home")} className={cn(buttonVariants({ variant: "ghost", size: "sm" }))}>
						<ArrowLeftIcon className="mr-2 h-4 w-4" />
						Home
					</Link>
					<Link href={route("login")} className={cn(buttonVariants({ variant: "ghost", size: "sm" }))}>
						Sign in
					</Link>
				</div>

				{/* Scrollable content */}
				<div className="flex-1 overflow-y-auto px-4 py-8 sm:px-8 lg:px-12">
					<div className="mx-auto max-w-2xl">
						<div className="mb-8">
							<h1 className="text-3xl font-bold tracking-tight sm:text-4xl">Privacy Policy</h1>
							<p className="mt-2 text-sm text-muted-foreground">Last updated: December 2025</p>
						</div>

						<div className="prose prose-lg prose-zinc dark:prose-invert">
							{policy || <p>This Privacy Policy describes how we collect, use, and handle your personal information when you use our services.</p>}
						</div>

						<p className="mt-12 text-center text-sm text-muted-foreground">
							Also see our{" "}
							<Link href={route("terms-of-service")} className="underline underline-offset-4 hover:text-primary">
								Terms of Service
							</Link>
						</p>
					</div>
				</div>

				{/* Fixed footer */}
				<Footer />
			</div>
		</>
	)
}

PrivacyPolicy.layout = (page: React.ReactNode) => <GuestLayout>{page}</GuestLayout>
