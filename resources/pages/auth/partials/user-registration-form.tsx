import { router, usePage } from "@inertiajs/react"
import { AlertCircle } from "lucide-react"
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

interface UserRegistrationFormProps extends React.HTMLAttributes<HTMLDivElement> {}

const registrationSchema = z.object({
	email: z.string().email({ message: "Username must be a valid email address" }),
	name: z.optional(z.string()),
	password: z.string().min(6, { message: "Password must be at least 6 characters." }),
})

export default function UserRegistrationForm({ className, ...props }: UserRegistrationFormProps) {
	const page = usePage<{
		githubOAuthEnabled: boolean
		googleOAuthEnabled: boolean
	}>()
	const { githubOAuthEnabled, googleOAuthEnabled } = page.props
	const flash = page.flash as FlashMessages | undefined
	const hasOAuthProviders = githubOAuthEnabled || googleOAuthEnabled

	const { form, isSubmitting, handleSubmit } = useInertiaForm({
		schema: registrationSchema,
		defaultValues: { email: "", name: "", password: "" },
		url: route("register.add"),
	})

	return (
		<div className={cn("grid gap-6", className)} {...props}>
			<Form {...form}>
				<form onSubmit={handleSubmit}>
					<div className="grid gap-2">
						{flash?.error && (
							<Alert variant="destructive">
								<AlertCircle className="h-4 w-4" />
								<AlertTitle>Error</AlertTitle>
								<AlertDescription>{flash.error.join("\n")}</AlertDescription>
							</Alert>
						)}

						<FormField
							control={form.control}
							name="name"
							render={({ field }) => (
								<FormItem>
									<FormLabel>Full Name</FormLabel>
									<FormControl>
										<Input placeholder="Your name (optional)" autoCapitalize="words" autoComplete="name" autoCorrect="off" {...field} disabled={isSubmitting} />
									</FormControl>
									<FormMessage />
								</FormItem>
							)}
						/>

						<FormField
							control={form.control}
							name="email"
							render={({ field }) => (
								<FormItem>
									<FormLabel>Email</FormLabel>
									<FormControl>
										<Input placeholder="name@example.com" autoCapitalize="none" autoComplete="email" autoCorrect="off" {...field} disabled={isSubmitting} />
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
											placeholder="Create a secure password"
											type="password"
											autoCapitalize="none"
											autoCorrect="off"
											autoComplete="new-password"
											{...field}
											disabled={isSubmitting}
										/>
									</FormControl>
									<FormMessage />
								</FormItem>
							)}
						/>

						<Button type="submit" className="mt-2 w-full" disabled={isSubmitting}>
							{isSubmitting && <Icons.spinner className="mr-2 h-4 w-4" />}
							Sign Up
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
						<Button variant="outline" type="button" disabled={isSubmitting} onClick={() => router.post(route("github.register"))}>
							{isSubmitting ? <Icons.spinner className="mr-2 h-4 w-4" /> : <Icons.gitHub className="mr-2 h-4 w-4" />} Sign up with GitHub
						</Button>
					)}
					{googleOAuthEnabled && (
						<Button variant="outline" type="button" disabled={isSubmitting} onClick={() => router.post(route("google.register"))}>
							{isSubmitting ? <Icons.spinner className="mr-2 h-4 w-4" /> : <Icons.google className="mr-2 h-4 w-4" />} Sign up with Google
						</Button>
					)}
				</>
			)}
		</div>
	)
}
