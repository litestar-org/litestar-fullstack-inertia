import { Head, Link } from "@inertiajs/react"
import { BeakerIcon, RocketIcon, ShieldCheckIcon, ZapIcon } from "lucide-react"
import { Icons } from "@/components/icons"
import { buttonVariants } from "@/components/ui/button"
import { RetroGrid } from "@/components/ui/retro-grid"
import { GuestLayout } from "@/layouts/guest-layout"
import { route } from "@/lib/generated/routes"
import { cn } from "@/lib/utils"

export default function Landing() {
	return (
		<>
			<Head title="Welcome to Litestar" />

			{/* Hero Panel - Left Side */}
			<div className="relative hidden h-full flex-col bg-muted p-10 text-foreground lg:flex dark:border-r">
				<RetroGrid />
				<Link href={route("home")} className="relative z-20">
					<div className="flex items-center font-medium text-lg">
						<Icons.logo className="mr-2 h-6 w-6" />
						Litestar Fullstack
					</div>
				</Link>

				<div className="relative z-20 mt-auto space-y-6">
					<div className="space-y-2">
						<h2 className="text-3xl font-bold tracking-tight">
							Build faster.
							<br />
							Ship with confidence.
						</h2>
						<p className="text-lg text-muted-foreground">The modern Python web framework for high-performance applications.</p>
					</div>

					<div className="grid gap-3">
						<div className="flex items-center gap-3">
							<div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
								<ZapIcon className="h-4 w-4 text-primary" />
							</div>
							<span className="text-sm">Lightning-fast async performance</span>
						</div>
						<div className="flex items-center gap-3">
							<div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
								<ShieldCheckIcon className="h-4 w-4 text-primary" />
							</div>
							<span className="text-sm">Built-in security and validation</span>
						</div>
						<div className="flex items-center gap-3">
							<div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
								<RocketIcon className="h-4 w-4 text-primary" />
							</div>
							<span className="text-sm">Seamless React SPA experience</span>
						</div>
					</div>
				</div>
			</div>

			{/* Content - Right Side */}
			<div className="flex h-full flex-col">
				{/* Fixed header */}
				<div className="sticky top-0 z-10 flex justify-end border-b bg-background/95 p-4 backdrop-blur supports-backdrop-filter:bg-background/60 md:p-6">
					<Link href={route("login")} className={cn(buttonVariants({ variant: "ghost", size: "sm" }))}>
						Sign in
					</Link>
				</div>

				<div className="flex-1 overflow-y-auto px-4 py-8 sm:px-8 lg:px-12">
					<div className="mx-auto max-w-2xl">
						<div className="mb-8 text-center lg:text-left">
							<h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
								Welcome to <span className="text-primary">Litestar</span>
							</h1>
							<p className="mt-4 text-lg text-muted-foreground">
								A reference application from the{" "}
								<a href="https://litestar.dev" target="_blank" className="font-semibold text-foreground hover:underline" rel="noreferrer">
									Litestar
								</a>{" "}
								team
							</p>
						</div>

						<div className="grid gap-4 sm:grid-cols-2">
							<a
								href="https://github.com/litestar-org/litestar-fullstack-inertia"
								className="group rounded-xl border bg-card p-6 transition-colors hover:bg-accent hover:text-foreground"
								target="_blank"
								rel="noreferrer"
							>
								<div className="flex items-center gap-3">
									<Icons.gitHub className="h-6 w-6 group-hover:text-foreground" />
									<span className="font-semibold">Litestar</span>
								</div>
								<p className="mt-3 text-sm text-muted-foreground group-hover:text-foreground/80">High-performance Python web framework. Contribute on GitHub.</p>
							</a>

							<a
								href="https://inertiajs.com/"
								className="group rounded-xl border bg-card p-6 transition-colors hover:bg-accent hover:text-foreground"
								target="_blank"
								rel="noreferrer"
							>
								<div className="flex items-center gap-3">
									<Icons.inertia className="h-6 w-6 group-hover:text-foreground" />
									<span className="font-semibold">Inertia.js</span>
								</div>
								<p className="mt-3 text-sm text-muted-foreground group-hover:text-foreground/80">Modern SPA experience with classic server-side routing.</p>
							</a>

							<a
								href="https://docs.advanced-alchemy.litestar.dev/latest/"
								className="group rounded-xl border bg-card p-6 transition-colors hover:bg-accent hover:text-foreground"
								target="_blank"
								rel="noreferrer"
							>
								<div className="flex items-center gap-3">
									<BeakerIcon className="h-6 w-6 group-hover:text-foreground" />
									<span className="font-semibold">Advanced Alchemy</span>
								</div>
								<p className="mt-3 text-sm text-muted-foreground group-hover:text-foreground/80">Optimized SQLAlchemy companion library.</p>
							</a>

							<a href="https://react.dev/" className="group rounded-xl border bg-card p-6 transition-colors hover:bg-accent hover:text-foreground" target="_blank" rel="noreferrer">
								<div className="flex items-center gap-3">
									<Icons.react className="h-6 w-6 group-hover:text-foreground" />
									<span className="font-semibold">React 19</span>
								</div>
								<p className="mt-3 text-sm text-muted-foreground group-hover:text-foreground/80">Modern UI with the latest React features.</p>
							</a>
						</div>

						<div className="mt-8 flex flex-col gap-4 sm:flex-row sm:justify-center lg:justify-start">
							<Link href={route("register")} className={cn(buttonVariants({ size: "lg" }))}>
								Get Started
							</Link>
							<a href="https://docs.litestar.dev" target="_blank" rel="noreferrer" className={cn(buttonVariants({ variant: "outline", size: "lg" }))}>
								Read the Docs
							</a>
						</div>

						<p className="mt-12 text-center text-sm text-muted-foreground lg:text-left">
							By entering this site, you agree to our{" "}
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
			</div>
		</>
	)
}

Landing.layout = (page: React.ReactNode) => <GuestLayout>{page}</GuestLayout>
