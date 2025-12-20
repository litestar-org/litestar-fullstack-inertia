import { Head, Link, useForm } from "@inertiajs/react"
import { AlertCircle, CheckCircle, LogIn, UserPlus, Users, XCircle } from "lucide-react"
import type React from "react"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { GuestLayout } from "@/layouts/guest-layout"
import type { InvitationAcceptPage } from "@/lib/generated/api/types.gen"
import { route } from "@/lib/generated/routes"

type Props = InvitationAcceptPage

export default function AcceptInvitation({ invitation, isValid, errorMessage, isAuthenticated, loginUrl, registerUrl }: Props) {
	const acceptForm = useForm({})
	const declineForm = useForm({})

	// Get token from URL
	const token = typeof window !== "undefined" ? window.location.pathname.split("/")[2] : ""

	const handleAccept = () => {
		acceptForm.post(route("invitation.accept", { token }), {
			preserveScroll: true,
		})
	}

	const handleDecline = () => {
		declineForm.post(route("invitation.decline", { token }), {
			preserveScroll: true,
		})
	}

	// Invalid invitation (expired, already accepted, or not found)
	if (!isValid) {
		return (
			<>
				<Head title="Invalid Invitation" />
				<Card className="w-full max-w-md">
					<CardHeader className="text-center">
						<div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-destructive/10">
							<XCircle className="h-8 w-8 text-destructive" />
						</div>
						<CardTitle>Invitation Not Valid</CardTitle>
						<CardDescription>This invitation cannot be accepted.</CardDescription>
					</CardHeader>
					<CardContent>
						<Alert variant="destructive">
							<AlertCircle className="h-4 w-4" />
							<AlertTitle>Error</AlertTitle>
							<AlertDescription>{errorMessage}</AlertDescription>
						</Alert>
					</CardContent>
					<CardFooter className="justify-center gap-2">
						{isAuthenticated ? (
							<Button variant="outline" asChild>
								<a href="/dashboard">Go to Dashboard</a>
							</Button>
						) : (
							<>
								<Button variant="outline" asChild>
									<Link href={loginUrl || "/login/"}>
										<LogIn className="mr-2 h-4 w-4" />
										Log In
									</Link>
								</Button>
								<Button asChild>
									<Link href={registerUrl || "/register/"}>
										<UserPlus className="mr-2 h-4 w-4" />
										Sign Up
									</Link>
								</Button>
							</>
						)}
					</CardFooter>
				</Card>
			</>
		)
	}

	// Unauthenticated user - show invitation details and prompt to login/signup
	if (!isAuthenticated) {
		return (
			<>
				<Head title={`Join ${invitation.teamName}`} />
				<Card className="w-full max-w-md">
					<CardHeader className="text-center">
						<div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
							<Users className="h-8 w-8 text-primary" />
						</div>
						<CardTitle>You're Invited!</CardTitle>
						<CardDescription>
							<strong>{invitation.inviterName}</strong> has invited you to join <strong>{invitation.teamName}</strong>
						</CardDescription>
					</CardHeader>
					<CardContent className="space-y-4">
						<div className="rounded-lg bg-muted p-4">
							<div className="space-y-2 text-sm">
								<div className="flex justify-between">
									<span className="text-muted-foreground">Team</span>
									<span className="font-medium">{invitation.teamName}</span>
								</div>
								<div className="flex justify-between">
									<span className="text-muted-foreground">Role</span>
									<span className="font-medium capitalize">{invitation.role}</span>
								</div>
								<div className="flex justify-between">
									<span className="text-muted-foreground">Invited by</span>
									<span className="font-medium">{invitation.inviterEmail}</span>
								</div>
							</div>
						</div>
						<Alert>
							<AlertCircle className="h-4 w-4" />
							<AlertTitle>Sign in required</AlertTitle>
							<AlertDescription>Log in or create an account to accept this invitation.</AlertDescription>
						</Alert>
					</CardContent>
					<CardFooter className="flex gap-3">
						<Button variant="outline" className="flex-1" asChild>
							<Link href={loginUrl || "/login/"}>
								<LogIn className="mr-2 h-4 w-4" />
								Log In
							</Link>
						</Button>
						<Button className="flex-1" asChild>
							<Link href={registerUrl || "/register/"}>
								<UserPlus className="mr-2 h-4 w-4" />
								Create Account
							</Link>
						</Button>
					</CardFooter>
				</Card>
			</>
		)
	}

	// Authenticated and correct user - show accept/decline
	return (
		<>
			<Head title={`Join ${invitation.teamName}`} />
			<Card className="w-full max-w-md">
				<CardHeader className="text-center">
					<div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
						<Users className="h-8 w-8 text-primary" />
					</div>
					<CardTitle>You're Invited!</CardTitle>
					<CardDescription>
						<strong>{invitation.inviterName}</strong> has invited you to join <strong>{invitation.teamName}</strong>
					</CardDescription>
				</CardHeader>
				<CardContent className="space-y-4">
					<div className="rounded-lg bg-muted p-4">
						<div className="space-y-2 text-sm">
							<div className="flex justify-between">
								<span className="text-muted-foreground">Team</span>
								<span className="font-medium">{invitation.teamName}</span>
							</div>
							<div className="flex justify-between">
								<span className="text-muted-foreground">Role</span>
								<span className="font-medium capitalize">{invitation.role}</span>
							</div>
							<div className="flex justify-between">
								<span className="text-muted-foreground">Invited by</span>
								<span className="font-medium">{invitation.inviterEmail}</span>
							</div>
						</div>
					</div>
				</CardContent>
				<CardFooter className="flex gap-3">
					<Button variant="outline" className="flex-1" onClick={handleDecline} disabled={declineForm.processing}>
						Decline
					</Button>
					<Button className="flex-1" onClick={handleAccept} disabled={acceptForm.processing}>
						<CheckCircle className="mr-2 h-4 w-4" />
						Accept Invitation
					</Button>
				</CardFooter>
			</Card>
		</>
	)
}

AcceptInvitation.layout = (page: React.ReactNode) => <GuestLayout>{page}</GuestLayout>
