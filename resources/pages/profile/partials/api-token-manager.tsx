import axios from "axios"
import { formatDistanceToNow } from "date-fns"
import { Copy, KeyRound, Loader2, Plus, RefreshCw, ShieldCheck, Trash2 } from "lucide-react"
import { useMemo, useState } from "react"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
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
import { Checkbox } from "@/components/ui/checkbox"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { toast } from "@/components/ui/use-toast"
import { cn } from "@/lib/utils"
import type { ApiTokenAbility, ApiTokenItem } from "@/pages/profile/api-tokens"

interface ApiTokenManagerProps {
	tokens: ApiTokenItem[]
	availableAbilities: ApiTokenAbility[]
	defaultAbilities: string[]
}

interface CreatedTokenState {
	token: string
	item: ApiTokenItem
}

function formatRelativeDate(value?: string | null) {
	return value ? formatDistanceToNow(new Date(value), { addSuffix: true }) : "Never"
}

export default function ApiTokenManager({ tokens: initialTokens, availableAbilities, defaultAbilities }: ApiTokenManagerProps) {
	const [tokens, setTokens] = useState<ApiTokenItem[]>(initialTokens)
	const [name, setName] = useState("")
	const [selectedAbilities, setSelectedAbilities] = useState<string[]>(defaultAbilities)
	const [isSubmitting, setIsSubmitting] = useState(false)
	const [createdToken, setCreatedToken] = useState<CreatedTokenState | null>(null)
	const [tokenToRevoke, setTokenToRevoke] = useState<ApiTokenItem | null>(null)
	const [isRevoking, setIsRevoking] = useState(false)

	const selectedAbilitySet = useMemo(() => new Set(selectedAbilities), [selectedAbilities])

	const toggleAbility = (ability: string) => {
		setSelectedAbilities((current) => (current.includes(ability) ? current.filter((value) => value !== ability) : [...current, ability]))
	}

	const copyToken = async () => {
		if (!createdToken) return
		await navigator.clipboard.writeText(createdToken.token)
		toast({ description: "Token copied to clipboard.", variant: "success" })
	}

	const createToken = async (event: React.FormEvent<HTMLFormElement>) => {
		event.preventDefault()
		if (!name.trim()) {
			toast({ description: "Token name is required.", variant: "destructive" })
			return
		}

		setIsSubmitting(true)
		try {
			const { data } = await axios.post<{ token: string; item: ApiTokenItem }>("/api-tokens/", {
				name: name.trim(),
				abilities: selectedAbilities,
			})
			setCreatedToken(data)
			setTokens((current) => [data.item, ...current.filter((token) => token.id !== data.item.id)])
			setName("")
			setSelectedAbilities(defaultAbilities)
			toast({ description: "API token created.", variant: "success" })
		} catch {
			toast({ description: "Failed to create API token.", variant: "destructive" })
		} finally {
			setIsSubmitting(false)
		}
	}

	const revokeToken = async () => {
		if (!tokenToRevoke) return

		setIsRevoking(true)
		try {
			await axios.delete(`/api-tokens/${tokenToRevoke.id}/`)
			setTokens((current) => current.filter((token) => token.id !== tokenToRevoke.id))
			if (createdToken?.item.id === tokenToRevoke.id) {
				setCreatedToken(null)
			}
			setTokenToRevoke(null)
			toast({ description: "API token revoked.", variant: "success" })
		} catch {
			toast({ description: "Failed to revoke API token.", variant: "destructive" })
		} finally {
			setIsRevoking(false)
		}
	}

	return (
		<div className="space-y-6">
			<div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
				<Card className="border-[#EDB641]/40 shadow-sm shadow-[#EDB641]/5">
					<CardHeader>
						<CardTitle className="flex items-center gap-2">
							<KeyRound className="h-5 w-5" />
							Create API Token
						</CardTitle>
						<CardDescription>Generate a scoped bearer token for integrations and automation. The plaintext token is shown only once.</CardDescription>
					</CardHeader>
					<CardContent>
						<form onSubmit={createToken} className="space-y-5">
							<div className="space-y-2">
								<Label htmlFor="token-name">Token name</Label>
								<Input
									id="token-name"
									placeholder="e.g. CI automation"
									value={name}
									onChange={(event) => setName(event.target.value)}
									disabled={isSubmitting}
								/>
							</div>

							<div className="space-y-3">
								<div className="flex items-center justify-between gap-3">
									<Label>Abilities</Label>
									<Button type="button" variant="ghost" size="sm" className="h-8 px-2 text-xs" onClick={() => setSelectedAbilities(defaultAbilities)} disabled={isSubmitting}>
										<RefreshCw className="mr-2 h-3.5 w-3.5" />
										Reset defaults
									</Button>
								</div>
								<div className="grid gap-3 md:grid-cols-2">
									{availableAbilities.map((ability) => {
										const checked = selectedAbilitySet.has(ability.value)
										return (
											<label
												key={ability.value}
												className={cn(
													"flex cursor-pointer items-start gap-3 rounded-lg border p-3 transition-colors",
													checked ? "border-primary/40 bg-primary/5" : "hover:bg-muted/50",
												)}
											>
												<Checkbox checked={checked} onCheckedChange={() => toggleAbility(ability.value)} disabled={isSubmitting} className="mt-0.5" />
												<div className="space-y-1">
													<div className="font-medium text-sm">{ability.label}</div>
													<div className="text-muted-foreground text-xs">{ability.description}</div>
												</div>
											</label>
										)
									})}
								</div>
							</div>

							<div className="flex flex-wrap items-center gap-3">
								<Button type="submit" disabled={isSubmitting}>
									{isSubmitting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Plus className="mr-2 h-4 w-4" />}
									Create token
								</Button>
								<p className="text-muted-foreground text-xs">Default abilities are pre-selected to keep the common case simple.</p>
							</div>
						</form>
					</CardContent>
				</Card>

				<div className="space-y-4">
					<Alert>
						<ShieldCheck className="h-4 w-4" />
						<AlertTitle>Token safety</AlertTitle>
						<AlertDescription>
							Store the plaintext token securely after creation. It cannot be shown again, only revoked and reissued.
						</AlertDescription>
					</Alert>

					{createdToken && (
						<Card className="border-emerald-500/30 bg-emerald-500/5">
							<CardHeader>
								<CardTitle className="flex items-center gap-2 text-emerald-700 dark:text-emerald-300">
									<Copy className="h-5 w-5" />
									New token value
								</CardTitle>
								<CardDescription>This plaintext token is visible only once.</CardDescription>
							</CardHeader>
							<CardContent className="space-y-4">
								<Textarea readOnly value={createdToken.token} className="min-h-28 font-mono text-xs" />
								<div className="flex flex-wrap gap-2">
									<Button type="button" variant="outline" onClick={copyToken}>
										<Copy className="mr-2 h-4 w-4" />
										Copy token
									</Button>
									<Button type="button" variant="ghost" onClick={() => setCreatedToken(null)}>
										Dismiss
									</Button>
								</div>
							</CardContent>
						</Card>
					)}
				</div>
			</div>

			<Card>
				<CardHeader>
					<CardTitle>Active Tokens</CardTitle>
					<CardDescription>
						{tokens.length ? `${tokens.length} token${tokens.length === 1 ? "" : "s"} available for API access.` : "You have not created any API tokens yet."}
					</CardDescription>
				</CardHeader>
				<CardContent className="space-y-3">
					{tokens.length === 0 ? (
						<div className="rounded-lg border border-dashed p-6 text-center text-muted-foreground text-sm">Create a token to unlock programmatic access.</div>
					) : (
						tokens.map((token) => (
							<div key={token.id} className="flex flex-col gap-4 rounded-lg border p-4 lg:flex-row lg:items-center lg:justify-between">
								<div className="space-y-2">
									<div className="flex flex-wrap items-center gap-2">
										<div className="font-semibold">{token.name}</div>
										{createdToken?.item.id === token.id && <Badge>Recently created</Badge>}
									</div>
									<div className="flex flex-wrap gap-2">
										<Badge variant="secondary">
											{token.abilities.length} {token.abilities.length === 1 ? "ability" : "abilities"}
										</Badge>
										{token.expiresAt ? <Badge variant="outline">Expires {formatRelativeDate(token.expiresAt)}</Badge> : <Badge variant="outline">No expiration</Badge>}
										<Badge variant="outline">Created {formatRelativeDate(token.createdAt)}</Badge>
									</div>
									<div className="flex flex-wrap gap-2">
										{token.abilities.map((ability) => (
											<Badge key={ability} variant="outline" className="rounded-full">
												{ability}
											</Badge>
										))}
									</div>
									<p className="text-muted-foreground text-sm">Last used {formatRelativeDate(token.lastUsedAt)}</p>
								</div>

								<div className="flex gap-2">
									<Button type="button" variant="destructive" onClick={() => setTokenToRevoke(token)}>
										<Trash2 className="mr-2 h-4 w-4" />
										Revoke
									</Button>
								</div>
							</div>
						))
					)}
				</CardContent>
			</Card>

			<AlertDialog open={!!tokenToRevoke} onOpenChange={(open) => !open && setTokenToRevoke(null)}>
				<AlertDialogContent>
					<AlertDialogHeader>
						<AlertDialogTitle>Revoke API token?</AlertDialogTitle>
						<AlertDialogDescription>
							This immediately disables the token named <span className="font-medium text-foreground">{tokenToRevoke?.name}</span>.
						</AlertDialogDescription>
					</AlertDialogHeader>
					<AlertDialogFooter>
						<AlertDialogCancel disabled={isRevoking}>Cancel</AlertDialogCancel>
						<AlertDialogAction onClick={revokeToken} disabled={isRevoking} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
							{isRevoking ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
							Revoke token
						</AlertDialogAction>
					</AlertDialogFooter>
				</AlertDialogContent>
			</AlertDialog>
		</div>
	)
}
