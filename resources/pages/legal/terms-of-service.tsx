import { Head, Link } from "@inertiajs/react"
import { ArrowLeftIcon } from "lucide-react"
import { AuthHeroPanel } from "@/components/auth-hero-panel"
import { buttonVariants } from "@/components/ui/button"
import { GuestLayout } from "@/layouts/guest-layout"
import Footer from "@/layouts/partials/footer"
import { route } from "@/lib/generated/routes"
import { cn } from "@/lib/utils"

interface Props {
	terms: string
}

export default function TermsOfService({ terms }: Props) {
	return (
		<>
			<Head title="Terms of Service" />

			<AuthHeroPanel title="Terms & Conditions" description="Please review the terms and conditions that govern your use of our services." showTestimonial={false} />

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
							<h1 className="text-3xl font-bold tracking-tight sm:text-4xl">Terms of Service</h1>
							<p className="mt-2 text-sm text-muted-foreground">Last updated: December 2025</p>
						</div>

						<div className="prose prose-lg prose-zinc dark:prose-invert">
							{terms || <p>These Terms of Service govern your access to and use of our services. By using our services, you agree to be bound by these terms.</p>}
						</div>

						<p className="mt-12 text-center text-sm text-muted-foreground">
							Also see our{" "}
							<Link href={route("privacy-policy")} className="underline underline-offset-4 hover:text-primary">
								Privacy Policy
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

TermsOfService.layout = (page: React.ReactNode) => <GuestLayout>{page}</GuestLayout>
