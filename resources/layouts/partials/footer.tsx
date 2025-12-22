import { ThemeToggle } from "@/components/theme-toggle"

export default function Footer() {
	const year = new Date().getFullYear()
	return (
		<footer className="border-t">
			<h2 id="footer-heading" className="sr-only">
				Footer
			</h2>
			<div className="mx-auto max-w-7xl px-6 py-8">
				<div className="md:flex md:items-center md:justify-between">
					<div className="flex space-x-6 md:order-2">
						<ThemeToggle />
					</div>
					<p className="mt-8 text-muted-foreground text-xs leading-5 md:order-1 md:mt-0">
						&copy; {year}{" "}
						<a href="https://litestar.dev/" className="font-semibold text-foreground">
							Litestar
						</a>
						. All rights reserved.
					</p>
				</div>
			</div>
		</footer>
	)
}
