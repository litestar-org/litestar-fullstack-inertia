import { Head } from "@inertiajs/react"
import type React from "react"
import { AppLayout } from "@/layouts/app-layout"

export default function About({ about: _about }: { about: string }) {
	return (
		<>
			<Head title="About Us" />
			<section className="relative flex w-full flex-1 items-center justify-center overflow-hidden">
				<div
					className="absolute inset-0 animate-starfield motion-reduce:animate-none"
					style={{
						backgroundImage: [
							"radial-gradient(1px 1px at 20% 30%, rgba(32,34,53,0.25) 0, transparent 60%)",
							"radial-gradient(1px 1px at 70% 20%, rgba(32,34,53,0.2) 0, transparent 60%)",
							"radial-gradient(1.5px 1.5px at 40% 60%, rgba(32,34,53,0.18) 0, transparent 60%)",
							"radial-gradient(1px 1px at 80% 75%, rgba(32,34,53,0.2) 0, transparent 60%)",
							"radial-gradient(1.5px 1.5px at 55% 85%, rgba(32,34,53,0.22) 0, transparent 60%)",
						].join(","),
					}}
				/>
				<div
					className="absolute inset-0 animate-twinkle motion-reduce:animate-none"
					style={{
						backgroundImage: [
							"radial-gradient(2px 2px at 12% 25%, rgba(32,34,53,0.4) 0, transparent 60%)",
							"radial-gradient(1.5px 1.5px at 28% 40%, rgba(32,34,53,0.35) 0, transparent 60%)",
							"radial-gradient(2px 2px at 68% 22%, rgba(32,34,53,0.4) 0, transparent 60%)",
							"radial-gradient(1.5px 1.5px at 82% 60%, rgba(32,34,53,0.35) 0, transparent 60%)",
							"radial-gradient(2px 2px at 45% 78%, rgba(32,34,53,0.35) 0, transparent 60%)",
						].join(","),
					}}
				/>
				<div
					className="absolute inset-0 animate-twinkle-fast motion-reduce:animate-none"
					style={{
						backgroundImage: [
							"radial-gradient(1.5px 1.5px at 18% 55%, rgba(32,34,53,0.35) 0, transparent 60%)",
							"radial-gradient(1px 1px at 33% 18%, rgba(32,34,53,0.3) 0, transparent 60%)",
							"radial-gradient(1.5px 1.5px at 57% 35%, rgba(32,34,53,0.35) 0, transparent 60%)",
							"radial-gradient(1px 1px at 76% 82%, rgba(32,34,53,0.3) 0, transparent 60%)",
							"radial-gradient(1.5px 1.5px at 90% 30%, rgba(32,34,53,0.35) 0, transparent 60%)",
						].join(","),
					}}
				/>
				<div className="absolute inset-0 bg-gradient-to-t from-background via-background/70 to-transparent" />
				<div
					className="absolute inset-0 animate-glow-pulse motion-reduce:animate-none"
					style={{
						backgroundImage: [
							"radial-gradient(2px 2px at 10% 15%, rgba(32,34,53,0.35) 0, transparent 60%)",
							"radial-gradient(1.5px 1.5px at 25% 45%, rgba(32,34,53,0.25) 0, transparent 60%)",
							"radial-gradient(1.5px 1.5px at 60% 30%, rgba(32,34,53,0.28) 0, transparent 60%)",
							"radial-gradient(2px 2px at 75% 55%, rgba(32,34,53,0.3) 0, transparent 60%)",
							"radial-gradient(1.5px 1.5px at 85% 20%, rgba(32,34,53,0.25) 0, transparent 60%)",
							"radial-gradient(2px 2px at 35% 80%, rgba(32,34,53,0.22) 0, transparent 60%)",
							"radial-gradient(1.5px 1.5px at 90% 85%, rgba(32,34,53,0.24) 0, transparent 60%)",
						].join(","),
					}}
				/>
				<div className="absolute inset-0 flex items-center justify-center">
					<div className="text-center text-sm font-semibold uppercase tracking-[0.3em] text-foreground/70">Made by the Litestar team</div>
				</div>
			</section>
		</>
	)
}

About.layout = (page: React.ReactNode) => <AppLayout mainClassName="pb-0 flex flex-col">{page}</AppLayout>
