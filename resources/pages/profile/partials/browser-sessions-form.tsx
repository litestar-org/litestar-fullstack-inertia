import { router } from "@inertiajs/react"
import { formatDistanceToNow } from "date-fns"
import { Loader2, Monitor, Smartphone, Tablet, ShieldAlert, LogOut } from "lucide-react"
import { useState } from "react"
import { Alert, AlertDescription } from "@/components/ui/alert"
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
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { toast } from "@/components/ui/use-toast"
import { cn } from "@/lib/utils"

interface BrowserSession {
	id: string
	sessionId: string
	ipAddress?: string | null
	browser: string
	os: string
	deviceType: string
	lastActivity: string
	isCurrent: boolean
}

interface BrowserSessionsFormProps {
	sessions: BrowserSession[]
}

function formatLastActive(lastActivity: string) {
	return formatDistanceToNow(new Date(lastActivity), { addSuffix: true })
}

function getDeviceIcon(deviceType: string) {
	switch (deviceType) {
		case "mobile":
			return Smartphone
		case "tablet":
			return Tablet
		default:
			return Monitor
	}
}

export default function BrowserSessionsForm({ sessions }: BrowserSessionsFormProps) {
	const [isDialogOpen, setIsDialogOpen] = useState(false)
	const [password, setPassword] = useState("")
	const [processing, setProcessing] = useState(false)
	const [error, setError] = useState<string | null>(null)

	const currentSessionCount = sessions.length
	const currentSession = sessions.find((session) => session.isCurrent)

	const handleLogoutOtherSessions = () => {
		setProcessing(true)
		setError(null)

		router.post(
			"/profile/browser-sessions/logout-others/",
			{ password },
			{
				preserveScroll: true,
				onSuccess: () => {
					setIsDialogOpen(false)
					setPassword("")
					toast({ description: "Other sessions were logged out.", variant: "success" })
				},
				onError: (errors) => {
					const message = Object.values(errors)[0]
					setError(typeof message === "string" ? message : "Failed to log out other sessions.")
				},
				onFinish: () => {
					setProcessing(false)
				},
			},
		)
	}

	return (
		<Card id="browser-sessions">
			<CardHeader>
				<CardTitle className="flex items-center gap-2">
					<ShieldAlert className="h-5 w-5" />
					Browser Sessions
				</CardTitle>
				<CardDescription>See where your account is signed in and remove other active sessions if needed.</CardDescription>
			</CardHeader>
			<CardContent className="space-y-4">
				<div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border bg-muted/30 p-4">
					<div>
						<div className="font-medium">{currentSessionCount} active session{currentSessionCount === 1 ? "" : "s"}</div>
						<p className="text-muted-foreground text-sm">{currentSession ? "Your current session is included in the list below." : "No tracked sessions were found for this account."}</p>
					</div>
					<Button type="button" variant="outline" onClick={() => setIsDialogOpen(true)} disabled={!currentSession || currentSessionCount <= 1}>
						<LogOut className="mr-2 h-4 w-4" />
						Log out other sessions
					</Button>
				</div>

				{sessions.length === 0 ? (
					<div className="rounded-lg border border-dashed p-6 text-center text-muted-foreground text-sm">Once you log in from a browser, your session details will appear here.</div>
				) : (
					<div className="space-y-3">
						{sessions.map((session) => {
							const Icon = getDeviceIcon(session.deviceType)
							return (
								<div key={session.id} className="flex flex-col gap-4 rounded-lg border p-4 md:flex-row md:items-start md:justify-between">
									<div className="flex items-start gap-3">
										<div className="flex h-10 w-10 items-center justify-center rounded-full bg-muted">
											<Icon className="h-5 w-5" />
										</div>
										<div className="space-y-1">
											<div className="flex flex-wrap items-center gap-2">
												<div className="font-medium">{session.browser}</div>
												{session.isCurrent ? <Badge>Current session</Badge> : <Badge variant="secondary">Other device</Badge>}
											</div>
											<div className="text-muted-foreground text-sm">{session.os}</div>
											<div className="text-muted-foreground text-sm">
												{session.ipAddress ? session.ipAddress : "IP unavailable"} · Last active {formatLastActive(session.lastActivity)}
											</div>
										</div>
									</div>
								</div>
							)
						})}
					</div>
				)}

				<Alert>
					<ShieldAlert className="h-4 w-4" />
					<AlertDescription>
						If you do not recognize a device, log out the other sessions and change your password right away.
					</AlertDescription>
				</Alert>
			</CardContent>

			<AlertDialog
				open={isDialogOpen}
				onOpenChange={(open) => {
					setIsDialogOpen(open)
					if (!open) {
						setPassword("")
						setError(null)
					}
				}}
			>
				<AlertDialogContent>
					<AlertDialogHeader>
						<AlertDialogTitle>Log out other sessions?</AlertDialogTitle>
						<AlertDialogDescription>
							Enter your password to end every session except the one you are currently using.
						</AlertDialogDescription>
					</AlertDialogHeader>
					<div className="space-y-2">
						<Label htmlFor="logout-other-password">Password</Label>
						<Input
							id="logout-other-password"
							type="password"
							autoComplete="current-password"
							value={password}
							onChange={(event) => setPassword(event.target.value)}
							disabled={processing}
						/>
						{error && <p className="text-destructive text-sm">{error}</p>}
					</div>
					<AlertDialogFooter>
						<AlertDialogCancel disabled={processing}>Cancel</AlertDialogCancel>
						<AlertDialogAction onClick={handleLogoutOtherSessions} disabled={processing || password.length === 0} className={cn("bg-destructive text-destructive-foreground hover:bg-destructive/90")}>
							{processing ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
							Log out others
						</AlertDialogAction>
					</AlertDialogFooter>
				</AlertDialogContent>
			</AlertDialog>
		</Card>
	)
}
