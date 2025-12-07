import { Head, useForm } from "@inertiajs/react"
import { route } from "litestar-vite-plugin/inertia-helpers"
import { useEffect } from "react"
import { InputError } from "@/components/input-error"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { GuestLayout } from "@/layouts/guest-layout"

export default function ConfirmPassword() {
	const { data, setData, post, processing, errors, reset } = useForm({
		password: "",
	})

	useEffect(() => {
		return () => {
			reset("password")
		}
	}, [reset])

	const submit = (e: { preventDefault: () => void }) => {
		e.preventDefault()

		post(route("password.confirm"))
	}

	return (
		<>
			<Head title="Confirm Password" />

			<div className="mb-4 text-muted-foreground text-sm">This is a secure area of the application. Please confirm your password before continuing.</div>

			<form onSubmit={submit}>
				<div className="mt-4">
					<Label htmlFor="password">Password</Label>

					<Input
						id="password"
						type="password"
						name="password"
						value={data.password}
						className="mt-1 block w-full"
						autoFocus
						onChange={(e) => setData("password", e.target.value)}
					/>

					<InputError message={errors.password} className="mt-2" />
				</div>

				<div className="mt-4 flex items-center justify-end">
					<Button className="ml-4" disabled={processing}>
						Confirm
					</Button>
				</div>
			</form>
		</>
	)
}

ConfirmPassword.layout = (page: any) => <GuestLayout>{page}</GuestLayout>
