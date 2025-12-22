import { router, useForm, usePage } from "@inertiajs/react"
import axios from "axios"
import { Copy, KeyRound, Loader2, QrCode, RefreshCw, ShieldCheck, ShieldOff } from "lucide-react"
import { useState } from "react"
import { InputError } from "@/components/input-error"
import {
	AlertDialog,
	AlertDialogAction,
	AlertDialogCancel,
	AlertDialogContent,
	AlertDialogDescription,
	AlertDialogFooter,
	AlertDialogHeader,
	AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { toast } from "@/components/ui/use-toast"
import type { User } from "@/lib/generated/api/types.gen"
import { route } from "@/lib/generated/routes"

interface MfaSetupResponse {
	secret: string
	qrCode: string
}

interface MfaBackupCodesResponse {
	codes: string[]
}

type SetupStep = "idle" | "qr" | "confirm" | "backup"

export default function MfaForm() {
	const { auth } = usePage<{ auth: { user: User } }>().props
	const user = auth.user

	const [setupStep, setSetupStep] = useState<SetupStep>("idle")
	const [setupData, setSetupData] = useState<MfaSetupResponse | null>(null)
	const [backupCodes, setBackupCodes] = useState<string[]>([])
	const [showDisableDialog, setShowDisableDialog] = useState(false)
	const [isEnabling, setIsEnabling] = useState(false)
	const [isRegenerating, setIsRegenerating] = useState(false)

	const confirmForm = useForm({ code: "" })
	const disableForm = useForm({ password: "" })

	const startSetup = async () => {
		setIsEnabling(true)
		try {
			const { data } = await axios.post<MfaSetupResponse>(route("mfa.enable"))
			setSetupData(data)
			setSetupStep("qr")
		} catch {
			toast({ description: "Failed to start MFA setup. Please try again.", variant: "destructive" })
		} finally {
			setIsEnabling(false)
		}
	}

	const confirmSetup = async (e: React.FormEvent) => {
		e.preventDefault()

		try {
			const { data } = await axios.post<MfaBackupCodesResponse>(route("mfa.confirm"), {
				code: confirmForm.data.code,
			})
			setBackupCodes(data.codes)
			setSetupStep("backup")
		} catch (error) {
			if (axios.isAxiosError(error) && error.response?.data?.detail) {
				confirmForm.setError("code", error.response.data.detail)
			} else {
				toast({ description: "Failed to confirm MFA. Please try again.", variant: "destructive" })
			}
		}
	}

	const disableMfa = () => {
		router.delete(route("mfa.disable"), {
			data: { password: disableForm.data.password },
			onSuccess: () => {
				setShowDisableDialog(false)
				disableForm.reset()
			},
			onError: (errors) => {
				const errorMessage = Object.values(errors)[0]
				if (errorMessage) {
					disableForm.setError("password", errorMessage)
				} else {
					toast({ description: "Failed to disable MFA. Please try again.", variant: "destructive" })
				}
			},
		})
	}

	const regenerateBackupCodes = async () => {
		setIsRegenerating(true)
		try {
			const { data } = await axios.post<MfaBackupCodesResponse>(route("mfa.regenerate-codes"))
			setBackupCodes(data.codes)
			setSetupStep("backup")
		} catch {
			toast({ description: "Failed to regenerate backup codes. Please try again.", variant: "destructive" })
		} finally {
			setIsRegenerating(false)
		}
	}

	const copyBackupCodes = () => {
		navigator.clipboard.writeText(backupCodes.join("\n"))
		toast({ description: "Backup codes copied to clipboard.", variant: "success" })
	}

	const closeSetup = () => {
		setSetupStep("idle")
		setSetupData(null)
		setBackupCodes([])
		confirmForm.reset()
		// Reload auth state after user has seen backup codes
		router.reload({ only: ["auth"] })
	}

	const isMfaEnabled = user.isTwoFactorEnabled

	return (
		<Card id="mfa">
			<CardHeader>
				<CardTitle className="flex items-center gap-2">
					{isMfaEnabled ? <ShieldCheck className="h-5 w-5 text-green-500" /> : <KeyRound className="h-5 w-5" />}
					Multi-Factor Authentication
				</CardTitle>
				<CardDescription>
					{isMfaEnabled ? "MFA is enabled. Your account is more secure." : "Add an extra layer of security to your account using multi-factor authentication."}
				</CardDescription>
			</CardHeader>
			<CardContent>
				{isMfaEnabled ? (
					<div className="space-y-4">
						<p className="text-muted-foreground text-sm">
							When MFA is enabled, you will be prompted for a secure, random token during authentication. You may retrieve this token from your phone's authenticator application.
						</p>
						<div className="flex flex-wrap gap-2">
							<Button variant="outline" onClick={regenerateBackupCodes} disabled={isRegenerating}>
								{isRegenerating ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <RefreshCw className="mr-2 h-4 w-4" />}
								Regenerate Recovery Codes
							</Button>
							<Button variant="destructive" onClick={() => setShowDisableDialog(true)}>
								<ShieldOff className="mr-2 h-4 w-4" />
								Disable
							</Button>
						</div>
					</div>
				) : (
					<div className="space-y-4">
						<p className="text-muted-foreground text-sm">
							When MFA is enabled, you will be prompted for a secure, random token during authentication. You may retrieve this token from your phone's authenticator application.
						</p>
						<Button onClick={startSetup} disabled={isEnabling}>
							{isEnabling ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <ShieldCheck className="mr-2 h-4 w-4" />}
							Enable MFA
						</Button>
					</div>
				)}
			</CardContent>

			{/* QR Code Dialog */}
			<Dialog open={setupStep === "qr"} onOpenChange={(open) => !open && closeSetup()}>
				<DialogContent>
					<DialogHeader>
						<DialogTitle className="flex items-center gap-2">
							<QrCode className="h-5 w-5" />
							Scan QR Code
						</DialogTitle>
						<DialogDescription>Scan this QR code with your authenticator app (like Google Authenticator, Authy, or 1Password).</DialogDescription>
					</DialogHeader>
					{setupData && (
						<div className="space-y-4">
							<div className="flex justify-center rounded-lg bg-white p-4">
								<img src={`data:image/png;base64,${setupData.qrCode}`} alt="MFA QR Code" className="h-48 w-48" />
							</div>
							<div className="space-y-2">
								<Label className="text-muted-foreground text-xs">Or enter this code manually:</Label>
								<code className="block rounded bg-muted p-2 text-center font-mono text-sm">{setupData.secret}</code>
							</div>
						</div>
					)}
					<DialogFooter>
						<Button variant="outline" onClick={closeSetup}>
							Cancel
						</Button>
						<Button onClick={() => setSetupStep("confirm")}>Continue</Button>
					</DialogFooter>
				</DialogContent>
			</Dialog>

			{/* Confirm Code Dialog */}
			<Dialog open={setupStep === "confirm"} onOpenChange={(open) => !open && closeSetup()}>
				<DialogContent>
					<form onSubmit={confirmSetup}>
						<DialogHeader>
							<DialogTitle>Verify Setup</DialogTitle>
							<DialogDescription>Enter the 6-digit code from your authenticator app to confirm setup.</DialogDescription>
						</DialogHeader>
						<div className="my-4">
							<Label htmlFor="confirm-code">Authentication Code</Label>
							<Input
								id="confirm-code"
								type="text"
								inputMode="numeric"
								pattern="[0-9]*"
								maxLength={6}
								value={confirmForm.data.code}
								onChange={(e) => confirmForm.setData("code", e.target.value.replace(/\D/g, ""))}
								className="mt-1 text-center font-mono text-lg tracking-widest"
								placeholder="000000"
								autoFocus
								autoComplete="one-time-code"
							/>
							<InputError message={confirmForm.errors.code} className="mt-2" />
						</div>
						<DialogFooter>
							<Button type="button" variant="outline" onClick={() => setSetupStep("qr")}>
								Back
							</Button>
							<Button type="submit" disabled={confirmForm.processing || confirmForm.data.code.length !== 6}>
								Confirm
							</Button>
						</DialogFooter>
					</form>
				</DialogContent>
			</Dialog>

			{/* Backup Codes Dialog */}
			<Dialog open={setupStep === "backup"} onOpenChange={(open) => !open && closeSetup()}>
				<DialogContent>
					<DialogHeader>
						<DialogTitle className="flex items-center gap-2 text-green-600">
							<ShieldCheck className="h-5 w-5" />
							MFA Enabled
						</DialogTitle>
						<DialogDescription>
							Save these recovery codes in a secure location. You can use these codes to access your account if you lose your authenticator device.
						</DialogDescription>
					</DialogHeader>
					<div className="space-y-4">
						<div className="grid grid-cols-2 gap-2 rounded-lg bg-muted p-4">
							{backupCodes.map((code) => (
								<code key={code} className="font-mono text-sm">
									{code}
								</code>
							))}
						</div>
						<Button variant="outline" className="w-full" onClick={copyBackupCodes}>
							<Copy className="mr-2 h-4 w-4" />
							Copy Codes
						</Button>
					</div>
					<DialogFooter>
						<Button onClick={closeSetup}>Done</Button>
					</DialogFooter>
				</DialogContent>
			</Dialog>

			{/* Disable MFA Dialog */}
			<AlertDialog open={showDisableDialog} onOpenChange={setShowDisableDialog}>
				<AlertDialogContent>
					<AlertDialogHeader>
						<AlertDialogTitle>Disable MFA</AlertDialogTitle>
						<AlertDialogDescription>This will make your account less secure. Please confirm your password to disable MFA.</AlertDialogDescription>
					</AlertDialogHeader>
					<div className="my-4">
						<Label htmlFor="disable-password">Password</Label>
						<Input
							id="disable-password"
							type="password"
							value={disableForm.data.password}
							onChange={(e) => disableForm.setData("password", e.target.value)}
							className="mt-1"
							autoFocus
						/>
						<InputError message={disableForm.errors.password} className="mt-2" />
					</div>
					<AlertDialogFooter>
						<AlertDialogCancel onClick={() => disableForm.reset()}>Cancel</AlertDialogCancel>
						<AlertDialogAction onClick={disableMfa} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
							Disable MFA
						</AlertDialogAction>
					</AlertDialogFooter>
				</AlertDialogContent>
			</AlertDialog>
		</Card>
	)
}
