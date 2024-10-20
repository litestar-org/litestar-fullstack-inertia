import { InputError } from "@/components/input-error"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { toast } from "@/components/ui/use-toast"
import { Transition } from "@headlessui/react"
import { Link, useForm, usePage } from "@inertiajs/react"
import { route } from "litestar-vite-plugin/inertia-helpers"

interface Props {
	mustVerifyEmail: boolean
	status?: string
	className?: string
}

export default function UpdateProfileInformation({ mustVerifyEmail, status }: Props) {
	const { auth } = usePage<InertiaProps>().props
	const { data, setData, patch, errors, processing, recentlySuccessful } = useForm({
		name: auth?.user?.name ?? "",
	})

	const submit = (e: { preventDefault: () => void }) => {
		e.preventDefault()
		patch(route("profile.update"), {
			preserveScroll: true,
			onSuccess: () => {
				console.log("Your profile information has been updated.")
				toast({
					description: "Your profile information has been updated.",
				})
			},
		})
	}

	return (
		<Card>
			<CardHeader>
				<CardTitle>Profile Information</CardTitle>
				<CardDescription>Update your account's profile information and email address.</CardDescription>
			</CardHeader>
			<CardContent>
				<form onSubmit={submit} className="space-y-6">
					<div>
						<Label htmlFor="email">Email</Label>

						<Input id="email" type="email" value={auth?.user?.email} className="mt-1" disabled />
					</div>
					<div>
						<Label htmlFor="name">Name</Label>

						<Input id="name" type="text" value={data.name} className="mt-1" onChange={(e) => setData("name", e.target.value)} required autoFocus autoComplete="name" />

						<InputError className="mt-2" message={errors.name} />
					</div>

					{mustVerifyEmail && auth?.user?.verifiedAt === null && (
						<div>
							<p className="mt-2 text-sm">
								Your email address is unverified.
								<Link href={route("verification.send")} method="post" as="button" className="text-muted-foreground underline hover:text-slate-900">
									Click here to re-send the verification email.
								</Link>
							</p>

							{status === "verification-link-sent" && <div className="mt-2 font-medium text-green-600 text-sm">A new verification link has been sent to your email address.</div>}
						</div>
					)}

					<div className="flex items-center gap-4">
						<Button disabled={processing}>Save</Button>

						<Transition show={recentlySuccessful} enterFrom="opacity-0" leaveTo="opacity-0" className="transition ease-in-out">
							<p className="text-muted-foreground text-sm">Saved.</p>
						</Transition>
					</div>
				</form>
			</CardContent>
		</Card>
	)
}
