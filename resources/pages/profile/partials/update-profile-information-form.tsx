import { zodResolver } from "@hookform/resolvers/zod"
import { Link, router, usePage } from "@inertiajs/react"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { toast } from "@/components/ui/use-toast"
import type { FullSharedProps } from "@/lib/generated/page-props"
import { route } from "@/lib/generated/routes"

interface Props {
	mustVerifyEmail: boolean
	status?: string
}

const profileSchema = z.object({
	name: z.string().min(1, "Name is required"),
})

type ProfileFormValues = z.infer<typeof profileSchema>

export default function UpdateProfileInformation({ mustVerifyEmail, status }: Props) {
	const { auth } = usePage<FullSharedProps>().props
	const [isSubmitting, setIsSubmitting] = useState(false)

	const form = useForm<ProfileFormValues>({
		resolver: zodResolver(profileSchema),
		defaultValues: {
			name: auth?.user?.name ?? "",
		},
	})

	function onSubmit(values: ProfileFormValues) {
		setIsSubmitting(true)
		router.patch(route("profile.update"), values, {
			preserveScroll: true,
			onSuccess: () => {
				toast({ description: "Your profile information has been updated." })
			},
			onError: (errors) => {
				if (errors.name) {
					form.setError("name", { message: errors.name as string })
				}
			},
			onFinish: () => setIsSubmitting(false),
		})
	}

	return (
		<Card>
			<CardHeader>
				<CardTitle>Profile Information</CardTitle>
				<CardDescription>Update your account's profile information and email address.</CardDescription>
			</CardHeader>
			<CardContent>
				<Form {...form}>
					<form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
						<FormField
							control={form.control}
							name="name"
							disabled
							render={() => (
								<FormItem>
									<FormLabel>Email</FormLabel>
									<FormControl>
										<Input type="email" value={auth?.user?.email ?? ""} disabled className="bg-muted" />
									</FormControl>
									<FormDescription>Your email address cannot be changed.</FormDescription>
								</FormItem>
							)}
						/>

						<FormField
							control={form.control}
							name="name"
							render={({ field }) => (
								<FormItem>
									<FormLabel>Name</FormLabel>
									<FormControl>
										<Input type="text" autoComplete="name" disabled={isSubmitting} {...field} />
									</FormControl>
									<FormMessage />
								</FormItem>
							)}
						/>

						{mustVerifyEmail && auth?.user && !("verifiedAt" in auth.user && auth.user.verifiedAt) && (
							<div className="rounded-md border border-amber-200 bg-amber-50 p-4 dark:border-amber-800 dark:bg-amber-950">
								<p className="text-sm text-amber-800 dark:text-amber-200">
									Your email address is unverified.{" "}
									<Link href={route("verify-email")} className="underline hover:no-underline">
										Click here to verify your email.
									</Link>
								</p>
								{status === "verification-link-sent" && (
									<p className="mt-2 font-medium text-green-600 text-sm dark:text-green-400">A new verification link has been sent to your email address.</p>
								)}
							</div>
						)}

						<Button type="submit" disabled={isSubmitting}>
							{isSubmitting ? "Saving..." : "Save"}
						</Button>
					</form>
				</Form>
			</CardContent>
		</Card>
	)
}
