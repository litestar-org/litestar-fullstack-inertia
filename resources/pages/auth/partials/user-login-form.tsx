import { router, usePage } from "@inertiajs/react"
import { AlertCircle } from "lucide-react"
import { useMemo, useState } from "react"
import { z } from "zod"
import { Icons } from "@/components/icons"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { useInertiaForm } from "@/hooks/use-inertia-form"
import type { FlashMessages } from "@/lib/generated/page-props"
import { route } from "@/lib/generated/routes"
import { cn } from "@/lib/utils"

interface UserLoginFormProps extends React.HTMLAttributes<HTMLDivElement> {}

const loginSchema = z.object({
	username: z.string().min(1, { message: "Username is required." }),
	password: z.string().min(1, "Please enter a valid password."),
	remember: z.boolean().default(false),
})

export default function UserLoginForm({ className, ...props }: UserLoginFormProps) {
	const page = usePage<{
		githubOAuthEnabled: boolean
		googleOAuthEnabled: boolean
	}>()
	const { githubOAuthEnabled, googleOAuthEnabled } = page.props
	const flash = page.flash as FlashMessages | undefined
	const hasOAuthProviders = githubOAuthEnabled || googleOAuthEnabled

	// Get error from URL query param (fallback when flash couldn't be set due to no session)
	// Use window.location directly since Inertia's url prop may not include query params on sessionless redirects
	const urlError = useMemo(() => {
		if (typeof window === "undefined") return null
		return new URLSearchParams(window.location.search).get("error")
	}, [])

	// Combined error: prefer flash, fall back to URL param
	const errorMessage = flash?.error?.length ? flash.error : urlError ? [urlError] : null

	const { form, isSubmitting, handleSubmit } = useInertiaForm({
		schema: loginSchema,
		defaultValues: { username: "", password: "", remember: false },
		url: route("login"),
	})

	const [oauthLoading, setOauthLoading] = useState(false)
	const isLoading = isSubmitting || oauthLoading

	return (
		<div className={cn("grid gap-6", className)} {...props}>
			<Form {...form}>
				<form onSubmit={handleSubmit}>
					<div className="grid gap-2">
						{errorMessage && (
							<Alert variant="destructive">
								<AlertCircle className="h-4 w-4" />
								<AlertTitle>Error</AlertTitle>
								<AlertDescription>{errorMessage.join("\n")}</AlertDescription>
							</Alert>
						)}

						<FormField
							control={form.control}
							name="username"
							render={({ field }) => (
								<FormItem>
									<FormLabel>Email</FormLabel>
									<FormControl>
										<Input placeholder="name@example.com" autoCapitalize="none" autoComplete="username" autoCorrect="off" {...field} disabled={isLoading} />
									</FormControl>
									<FormMessage />
								</FormItem>
							)}
						/>

						<FormField
							control={form.control}
							name="password"
							render={({ field }) => (
								<FormItem>
									<FormLabel>Password</FormLabel>
									<FormControl>
										<Input
											placeholder="Enter your password"
											type="password"
											autoCapitalize="none"
											autoCorrect="off"
											autoComplete="current-password"
											{...field}
											disabled={isLoading}
										/>
									</FormControl>
									<FormMessage />
								</FormItem>
							)}
						/>

						<Button type="submit" className="mt-2 w-full" disabled={isLoading}>
							{isLoading && <Icons.spinner className="mr-2 h-4 w-4" />}
							Sign In
						</Button>
					</div>
				</form>
			</Form>
			{hasOAuthProviders && (
				<>
					<div className="relative">
						<div className="absolute inset-0 flex items-center">
							<span className="w-full border-t" />
						</div>
						<div className="relative flex justify-center text-xs uppercase">
							<span className="bg-background px-2 text-muted-foreground">Or continue with</span>
						</div>
					</div>
					{githubOAuthEnabled && (
						<Button
							variant="outline"
							type="button"
							disabled={isLoading}
							onClick={() => {
								setOauthLoading(true)
								router.post(route("github.register"))
							}}
						>
							{isLoading ? <Icons.spinner className="mr-2 h-4 w-4" /> : <Icons.gitHub className="mr-2 h-4 w-4" />}
							Continue with GitHub
						</Button>
					)}
					{googleOAuthEnabled && (
						<Button
							variant="outline"
							type="button"
							disabled={isLoading}
							onClick={() => {
								setOauthLoading(true)
								router.post(route("google.register"))
							}}
						>
							{isLoading ? <Icons.spinner className="mr-2 h-4 w-4" /> : <Icons.google className="mr-2 h-4 w-4" />}
							Continue with Google
						</Button>
					)}
				</>
			)}
		</div>
	)
}
