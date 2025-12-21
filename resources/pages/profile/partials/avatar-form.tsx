import { router, usePage } from "@inertiajs/react"
import { Camera, Loader2, Trash2 } from "lucide-react"
import { useRef, useState } from "react"
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
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { toast } from "@/components/ui/use-toast"
import type { FullSharedProps } from "@/lib/generated/page-props"
import { route } from "@/lib/generated/routes"

const ALLOWED_TYPES = ["image/jpeg", "image/png", "image/gif", "image/webp"]
const MAX_SIZE = 5 * 1024 * 1024 // 5MB

export default function AvatarForm() {
	const { auth, csrf_token } = usePage<FullSharedProps>().props
	const [isUploading, setIsUploading] = useState(false)
	const [isDeleting, setIsDeleting] = useState(false)
	const fileInputRef = useRef<HTMLInputElement>(null)

	const user = auth?.user
	const avatarUrl = user?.avatarUrl
	const isGravatar = avatarUrl?.includes("gravatar.com")

	function getInitials(name?: string | null, email?: string): string {
		if (name) {
			return name
				.split(" ")
				.map((n) => n[0])
				.join("")
				.toUpperCase()
				.slice(0, 2)
		}
		return email?.charAt(0).toUpperCase() ?? "U"
	}

	function handleFileSelect() {
		fileInputRef.current?.click()
	}

	async function handleFileChange(event: React.ChangeEvent<HTMLInputElement>) {
		const file = event.target.files?.[0]
		if (!file) return

		// Client-side validation
		if (!ALLOWED_TYPES.includes(file.type)) {
			toast({
				variant: "destructive",
				description: "Invalid file type. Please use JPEG, PNG, GIF, or WebP.",
			})
			return
		}

		if (file.size > MAX_SIZE) {
			toast({
				variant: "destructive",
				description: "File too large. Maximum size is 5MB.",
			})
			return
		}

		setIsUploading(true)

		try {
			const formData = new FormData()
			formData.append("data", file)

			const response = await fetch(route("profile.avatar.upload"), {
				method: "POST",
				headers: {
					"X-CSRFToken": csrf_token ?? "",
				},
				body: formData,
			})

			if (!response.ok) {
				const errorData = await response.json()
				throw new Error(errorData.detail || "Upload failed")
			}

			toast({ description: "Avatar updated successfully." })
			router.reload({ only: ["auth"] })
		} catch (error) {
			toast({
				variant: "destructive",
				description: error instanceof Error ? error.message : "Failed to upload avatar.",
			})
		} finally {
			setIsUploading(false)
			// Reset file input
			if (fileInputRef.current) {
				fileInputRef.current.value = ""
			}
		}
	}

	async function handleDelete() {
		setIsDeleting(true)

		try {
			const response = await fetch(route("profile.avatar.delete"), {
				method: "DELETE",
				headers: {
					"X-CSRFToken": csrf_token ?? "",
					"Content-Type": "application/json",
				},
			})

			if (!response.ok) {
				const errorData = await response.json()
				throw new Error(errorData.detail || "Delete failed")
			}

			toast({ description: "Avatar removed. Using Gravatar." })
			router.reload({ only: ["auth"] })
		} catch (error) {
			toast({
				variant: "destructive",
				description: error instanceof Error ? error.message : "Failed to remove avatar.",
			})
		} finally {
			setIsDeleting(false)
		}
	}

	return (
		<Card>
			<CardHeader>
				<CardTitle>Profile Picture</CardTitle>
				<CardDescription>Upload a custom avatar or use your Gravatar.</CardDescription>
			</CardHeader>
			<CardContent>
				<div className="flex items-center gap-6">
					<div className="relative">
						<Avatar className="h-24 w-24">
							<AvatarImage src={avatarUrl ?? undefined} alt={user?.name ?? user?.email} />
							<AvatarFallback className="text-2xl">{getInitials(user?.name, user?.email)}</AvatarFallback>
						</Avatar>
						<Button
							type="button"
							variant="secondary"
							size="icon"
							className="-right-1 -bottom-1 absolute h-8 w-8 rounded-full shadow-md"
							onClick={handleFileSelect}
							disabled={isUploading || isDeleting}
						>
							{isUploading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Camera className="h-4 w-4" />}
						</Button>
					</div>

					<div className="flex flex-col gap-2">
						<div className="flex gap-2">
							<Button type="button" variant="outline" size="sm" onClick={handleFileSelect} disabled={isUploading || isDeleting}>
								{isUploading ? (
									<>
										<Loader2 className="mr-2 h-4 w-4 animate-spin" />
										Uploading...
									</>
								) : (
									"Upload new avatar"
								)}
							</Button>

							{!isGravatar && (
								<AlertDialog>
									<AlertDialogTrigger asChild>
										<Button type="button" variant="ghost" size="sm" disabled={isUploading || isDeleting}>
											{isDeleting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Trash2 className="mr-2 h-4 w-4" />}
											Remove
										</Button>
									</AlertDialogTrigger>
									<AlertDialogContent>
										<AlertDialogHeader>
											<AlertDialogTitle>Remove Avatar</AlertDialogTitle>
											<AlertDialogDescription>Are you sure you want to remove your custom avatar? Your Gravatar will be used instead.</AlertDialogDescription>
										</AlertDialogHeader>
										<AlertDialogFooter>
											<AlertDialogCancel>Cancel</AlertDialogCancel>
											<AlertDialogAction onClick={handleDelete}>Remove</AlertDialogAction>
										</AlertDialogFooter>
									</AlertDialogContent>
								</AlertDialog>
							)}
						</div>
						<p className="text-muted-foreground text-xs">JPEG, PNG, GIF, or WebP. Max 5MB.</p>
						{isGravatar && <p className="text-muted-foreground text-xs">Currently using Gravatar based on your email.</p>}
					</div>
				</div>

				<input ref={fileInputRef} type="file" accept="image/jpeg,image/png,image/gif,image/webp" onChange={handleFileChange} className="hidden" />
			</CardContent>
		</Card>
	)
}
