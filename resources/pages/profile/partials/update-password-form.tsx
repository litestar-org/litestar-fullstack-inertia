import { z } from "zod"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { toast } from "@/components/ui/use-toast"
import { useInertiaForm } from "@/hooks/use-inertia-form"
import { route } from "@/lib/generated/routes"

const passwordSchema = z
	.object({
		currentPassword: z.string().min(1, "Current password is required"),
		newPassword: z.string().min(8, "Password must be at least 8 characters"),
		passwordConfirmation: z.string().min(1, "Please confirm your password"),
	})
	.refine((data) => data.newPassword === data.passwordConfirmation, {
		message: "Passwords do not match",
		path: ["passwordConfirmation"],
	})

export default function UpdatePasswordForm() {
	const { form, isSubmitting, handleSubmit, reset } = useInertiaForm({
		schema: passwordSchema,
		defaultValues: {
			currentPassword: "",
			newPassword: "",
			passwordConfirmation: "",
		},
		url: route("password.update"),
		method: "patch",
		// Only send fields the backend expects (not passwordConfirmation)
		transform: ({ currentPassword, newPassword }) => ({ currentPassword, newPassword }),
		onSuccess: () => {
			toast({ description: "Your password has been updated." })
			reset()
		},
	})

	return (
		<Card>
			<CardHeader>
				<CardTitle>Update Password</CardTitle>
				<CardDescription>Ensure your account is using a long, random password to stay secure.</CardDescription>
			</CardHeader>
			<CardContent>
				<Form {...form}>
					<form onSubmit={handleSubmit} className="space-y-4">
						<FormField
							control={form.control}
							name="currentPassword"
							render={({ field }) => (
								<FormItem>
									<FormLabel>Current Password</FormLabel>
									<FormControl>
										<Input type="password" autoComplete="current-password" disabled={isSubmitting} {...field} />
									</FormControl>
									<FormMessage />
								</FormItem>
							)}
						/>

						<FormField
							control={form.control}
							name="newPassword"
							render={({ field }) => (
								<FormItem>
									<FormLabel>New Password</FormLabel>
									<FormControl>
										<Input type="password" autoComplete="new-password" disabled={isSubmitting} {...field} />
									</FormControl>
									<FormMessage />
								</FormItem>
							)}
						/>

						<FormField
							control={form.control}
							name="passwordConfirmation"
							render={({ field }) => (
								<FormItem>
									<FormLabel>Confirm Password</FormLabel>
									<FormControl>
										<Input type="password" autoComplete="new-password" disabled={isSubmitting} {...field} />
									</FormControl>
									<FormMessage />
								</FormItem>
							)}
						/>

						<Button type="submit" disabled={isSubmitting}>
							{isSubmitting ? "Saving..." : "Save"}
						</Button>
					</form>
				</Form>
			</CardContent>
		</Card>
	)
}
