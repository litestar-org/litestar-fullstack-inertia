import { router } from "@inertiajs/react"
import { useState } from "react"
import {
	AlertDialog,
	AlertDialogAction,
	AlertDialogCancel,
	AlertDialogContent,
	AlertDialogDescription,
	AlertDialogFooter,
	AlertDialogHeader,
	AlertDialogTitle,
	AlertDialogTrigger,
} from "@/components/ui/alert-dialog"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { route } from "@/lib/generated/routes"

export default function DeleteUserForm() {
	const [isDeleting, setIsDeleting] = useState(false)
	const [isOpen, setIsOpen] = useState(false)

	function handleDelete() {
		setIsDeleting(true)
		router.delete(route("account.remove"), {
			preserveScroll: true,
			onSuccess: () => {
				setIsOpen(false)
			},
			onFinish: () => setIsDeleting(false),
		})
	}

	return (
		<Card className="border-destructive/50">
			<CardHeader>
				<CardTitle>Delete Account</CardTitle>
				<CardDescription>
					Once your account is deleted, all of its resources and data will be permanently deleted. Before deleting your account, please download any data or information that you
					wish to retain.
				</CardDescription>
			</CardHeader>
			<CardContent>
				<AlertDialog open={isOpen} onOpenChange={setIsOpen}>
					<AlertDialogTrigger asChild>
						<Button variant="destructive">Delete Account</Button>
					</AlertDialogTrigger>
					<AlertDialogContent>
						<AlertDialogHeader>
							<AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
							<AlertDialogDescription>This action cannot be undone. This will permanently delete your account and remove all of your data from our servers.</AlertDialogDescription>
						</AlertDialogHeader>
						<AlertDialogFooter>
							<AlertDialogCancel disabled={isDeleting}>Cancel</AlertDialogCancel>
							<AlertDialogAction onClick={handleDelete} disabled={isDeleting} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
								{isDeleting ? "Deleting..." : "Delete Account"}
							</AlertDialogAction>
						</AlertDialogFooter>
					</AlertDialogContent>
				</AlertDialog>
			</CardContent>
		</Card>
	)
}
