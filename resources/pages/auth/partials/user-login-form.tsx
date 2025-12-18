import { zodResolver } from "@hookform/resolvers/zod"
import { router, usePage } from "@inertiajs/react"
import { AlertCircle } from "lucide-react"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { toast } from "sonner"
import { z } from "zod"
import { Icons } from "@/components/icons"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { route } from "@/lib/generated/routes"
import { cn } from "@/lib/utils"
import type { FlashMessages } from "@/types"

interface UserLoginFormProps extends React.HTMLAttributes<HTMLDivElement> {}
const formSchema = z.object({
	username: z.string().min(1, {
		message: "Username is required.",
	}),
	password: z.string().min(1, "Please enter a valid password."),
	remember: z.boolean().default(false),
})

type FormProps = z.infer<typeof formSchema>

export default function UserLoginForm({ className, ...props }: UserLoginFormProps) {
	const { content, flash, githubOAuthEnabled, googleOAuthEnabled } = usePage<{
		content: {
			status_code: number
			message: string
		}
		flash: FlashMessages
		githubOAuthEnabled: boolean
		googleOAuthEnabled: boolean
	}>().props
	const hasOAuthProviders = githubOAuthEnabled || googleOAuthEnabled
	const [isLoading, setIsLoading] = useState<boolean>(false)
	const form = useForm<FormProps>({
		resolver: zodResolver(formSchema),
		defaultValues: {
			username: "",
			password: "",
		},
	})

	async function onSubmit(values: FormProps) {
		try {
			setIsLoading(true)
			router.post(route("login"), values, {
				onError: (err) => {
					console.log(err)
					if ("username" in err && typeof err.username === "string") {
						form.setError("root", { message: err.username })
					}
				},
			})
		} catch (error: any) {
			console.log(error)
			toast(content?.message ?? error.response?.data?.detail ?? "There was an unexpected error logging in.")
		} finally {
			setIsLoading(false)
		}
	}
	return (
		<div className={cn("grid gap-6", className)} {...props}>
			<Form {...form}>
				<form onSubmit={form.handleSubmit(onSubmit)}>
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
						<Button variant="outline" type="button" disabled={isLoading} onClick={() => router.post(route("github.register"))}>
							{isLoading ? <Icons.spinner className="mr-2 h-4 w-4" /> : <Icons.gitHub className="mr-2 h-4 w-4" />}
							Continue with GitHub
						</Button>
					)}
					{googleOAuthEnabled && (
						<Button variant="outline" type="button" disabled={isLoading} onClick={() => router.post(route("google.register"))}>
							{isLoading ? <Icons.spinner className="mr-2 h-4 w-4" /> : <Icons.google className="mr-2 h-4 w-4" />}
							Continue with Google
						</Button>
					)}
				</>
			)}
		</div>
	)
}
