import { Head, useForm } from "@inertiajs/react"
import { useState } from "react"
import { AuthHeroPanel } from "@/components/auth-hero-panel"
import { Icons } from "@/components/icons"
import { InputError } from "@/components/input-error"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { GuestLayout } from "@/layouts/guest-layout"
import { route } from "@/lib/generated/routes"

export default function MfaChallenge() {
	const [useRecoveryCode, setUseRecoveryCode] = useState(false)

	const { data, setData, post, processing, errors } = useForm({
		code: "",
		recovery_code: "",
	})

	const submit = (e: React.FormEvent) => {
		e.preventDefault()
		post(route("mfa-challenge.verify"))
	}

	return (
		<>
			<Head title="Multi-Factor Authentication" />

			<AuthHeroPanel title="Litestar Fullstack" description="Secure your account with multi-factor authentication." />

			<div className="flex flex-col justify-center px-4 py-8 sm:px-6 lg:px-8">
				<div className="mx-auto flex w-full flex-col justify-center space-y-6 sm:w-87.5">
					<div className="flex flex-col space-y-2 text-center">
						<h1 className="flex items-center justify-center gap-2 font-semibold text-2xl tracking-tight">
							<Icons.shield className="h-5 w-5" />
							Multi-Factor Authentication
						</h1>
						<p className="text-muted-foreground text-sm">
							{useRecoveryCode ? "Enter one of your emergency recovery codes to access your account." : "Enter the 6-digit code from your authenticator app to continue."}
						</p>
					</div>

					<form onSubmit={submit} className="space-y-4">
						{useRecoveryCode ? (
							<div>
								<Label htmlFor="recovery_code">Recovery Code</Label>
								<Input
									id="recovery_code"
									type="text"
									value={data.recovery_code}
									onChange={(e) => setData("recovery_code", e.target.value.toUpperCase())}
									className="mt-1 font-mono tracking-widest"
									placeholder="XXXXXXXX"
									autoFocus
									autoComplete="off"
								/>
								<InputError message={errors.recovery_code} className="mt-2" />
							</div>
						) : (
							<div>
								<Label htmlFor="code">Authentication Code</Label>
								<Input
									id="code"
									type="text"
									inputMode="numeric"
									pattern="[0-9]*"
									maxLength={6}
									value={data.code}
									onChange={(e) => setData("code", e.target.value.replace(/\D/g, ""))}
									className="mt-1 text-center font-mono text-lg tracking-widest"
									placeholder="000000"
									autoFocus
									autoComplete="one-time-code"
								/>
								<InputError message={errors.code} className="mt-2" />
							</div>
						)}

						<Button type="submit" className="w-full" disabled={processing}>
							Verify
						</Button>
					</form>

					<div className="text-center">
						<button
							type="button"
							onClick={() => {
								setUseRecoveryCode(!useRecoveryCode)
								setData(useRecoveryCode ? { code: "", recovery_code: "" } : { code: "", recovery_code: "" })
							}}
							className="text-muted-foreground text-sm underline-offset-4 hover:text-primary hover:underline"
						>
							{useRecoveryCode ? "Use authentication code instead" : "Use a recovery code"}
						</button>
					</div>
				</div>
			</div>
		</>
	)
}

MfaChallenge.layout = (page: React.ReactNode) => <GuestLayout>{page}</GuestLayout>
