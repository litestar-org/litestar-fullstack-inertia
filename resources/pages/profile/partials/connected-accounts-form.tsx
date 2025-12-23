import { router, usePage } from "@inertiajs/react"
import { Link2, Link2Off, Loader2 } from "lucide-react"
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
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { toast } from "@/components/ui/use-toast"
import type { User } from "@/lib/generated/api/types.gen"
import { route } from "@/lib/generated/routes"

// Simple OAuth provider icons
function GitHubIcon({ className }: { className?: string }) {
	return (
		<svg className={className} viewBox="0 0 24 24" fill="currentColor" aria-label="GitHub">
			<path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z" />
		</svg>
	)
}

function GoogleIcon({ className }: { className?: string }) {
	return (
		<svg className={className} viewBox="0 0 24 24" aria-label="Google">
			<path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
			<path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
			<path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
			<path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
		</svg>
	)
}

interface OAuthAccount {
	id: string
	oauthName: string
	accountId: string
	accountEmail: string
	scopes?: string[] | null
}

interface OAuthProviderRowProps {
	provider: "github" | "google"
	label: string
	icon: React.ReactNode
	account: OAuthAccount | undefined
	canUnlink: boolean
	isEnabled: boolean
	onLink: () => void
	onUnlink: () => void
}

function OAuthProviderRow({ provider: _provider, label, icon, account, canUnlink, isEnabled, onLink, onUnlink }: OAuthProviderRowProps) {
	const isConnected = !!account
	const [isLinking, setIsLinking] = useState(false)

	const handleLink = () => {
		setIsLinking(true)
		onLink()
	}

	if (!isEnabled) {
		return null
	}

	return (
		<div className="flex items-center justify-between p-4 border rounded-lg">
			<div className="flex items-center gap-3">
				<div className="w-8 h-8 flex items-center justify-center">{icon}</div>
				<div>
					<p className="font-medium">{label}</p>
					{isConnected ? <p className="text-sm text-muted-foreground">{account.accountEmail}</p> : <p className="text-sm text-muted-foreground">Not connected</p>}
				</div>
			</div>

			<div className="flex items-center gap-2">
				{isConnected ? (
					<Button
						variant="destructive"
						size="sm"
						onClick={onUnlink}
						disabled={!canUnlink}
						title={!canUnlink ? "Cannot unlink your only login method. Please set a password first." : undefined}
					>
						<Link2Off className="mr-2 h-4 w-4" />
						Unlink
					</Button>
				) : (
					<Button variant="outline" size="sm" onClick={handleLink} disabled={isLinking}>
						{isLinking ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Link2 className="mr-2 h-4 w-4" />}
						Connect
					</Button>
				)}
			</div>
		</div>
	)
}

export default function ConnectedAccountsForm() {
	const { auth, githubOAuthEnabled, googleOAuthEnabled } = usePage<{
		auth: { user: User }
		githubOAuthEnabled: boolean
		googleOAuthEnabled: boolean
	}>().props

	const user = auth.user
	const oauthAccounts = (user.oauthAccounts || []) as OAuthAccount[]

	const [unlinkProvider, setUnlinkProvider] = useState<string | null>(null)
	const [isUnlinking, setIsUnlinking] = useState(false)

	// Check if user can unlink (has password OR has multiple OAuth accounts)
	const canUnlink = user.hasPassword || oauthAccounts.length > 1

	// Find connected accounts
	const githubAccount = oauthAccounts.find((a) => a.oauthName === "github")
	const googleAccount = oauthAccounts.find((a) => a.oauthName === "google")

	const handleLink = (provider: string) => {
		router.post(route("oauth.link.start", { provider }))
	}

	const handleUnlink = () => {
		if (!unlinkProvider) return

		setIsUnlinking(true)
		router.delete(route("oauth.unlink", { provider: unlinkProvider }), {
			onSuccess: () => {
				toast({ description: `Successfully disconnected ${unlinkProvider} account.`, variant: "success" })
				setUnlinkProvider(null)
			},
			onError: (errors) => {
				const errorMessage = Object.values(errors)[0]
				toast({ description: errorMessage || "Failed to disconnect account.", variant: "destructive" })
			},
			onFinish: () => {
				setIsUnlinking(false)
			},
		})
	}

	// Check if any OAuth providers are enabled
	if (!githubOAuthEnabled && !googleOAuthEnabled) {
		return null
	}

	return (
		<Card id="connected-accounts">
			<CardHeader>
				<CardTitle className="flex items-center gap-2">
					<Link2 className="h-5 w-5" />
					Connected Accounts
				</CardTitle>
				<CardDescription>Manage your connected OAuth providers for login.</CardDescription>
			</CardHeader>
			<CardContent className="space-y-4">
				{/* GitHub */}
				<OAuthProviderRow
					provider="github"
					label="GitHub"
					icon={<GitHubIcon className="h-6 w-6" />}
					account={githubAccount}
					canUnlink={canUnlink}
					isEnabled={githubOAuthEnabled}
					onLink={() => handleLink("github")}
					onUnlink={() => setUnlinkProvider("github")}
				/>

				{/* Google */}
				<OAuthProviderRow
					provider="google"
					label="Google"
					icon={<GoogleIcon className="h-6 w-6" />}
					account={googleAccount}
					canUnlink={canUnlink}
					isEnabled={googleOAuthEnabled}
					onLink={() => handleLink("google")}
					onUnlink={() => setUnlinkProvider("google")}
				/>

				{/* Warning when OAuth is only auth method */}
				{!user.hasPassword && oauthAccounts.length === 1 && (
					<Alert>
						<AlertDescription>You can only log in using {oauthAccounts[0].oauthName}. Set a password in the Password section above to enable unlinking.</AlertDescription>
					</Alert>
				)}
			</CardContent>

			{/* Unlink Confirmation Dialog */}
			<AlertDialog open={!!unlinkProvider} onOpenChange={(open) => !open && setUnlinkProvider(null)}>
				<AlertDialogContent>
					<AlertDialogHeader>
						<AlertDialogTitle>Disconnect {unlinkProvider}?</AlertDialogTitle>
						<AlertDialogDescription>
							You will no longer be able to log in using your {unlinkProvider} account. Make sure you have another way to access your account.
						</AlertDialogDescription>
					</AlertDialogHeader>
					<AlertDialogFooter>
						<AlertDialogCancel disabled={isUnlinking}>Cancel</AlertDialogCancel>
						<AlertDialogAction onClick={handleUnlink} disabled={isUnlinking} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
							{isUnlinking ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
							Disconnect
						</AlertDialogAction>
					</AlertDialogFooter>
				</AlertDialogContent>
			</AlertDialog>
		</Card>
	)
}
