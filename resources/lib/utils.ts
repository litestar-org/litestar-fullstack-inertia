import type { ErrorBag, Errors } from "@inertiajs/core"
import { type ClassValue, clsx } from "clsx"
import md5 from "md5"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
	return twMerge(clsx(inputs))
}

export function strLimit(value: string, limit: number, end = "...") {
	return value.length > limit ? value.substring(0, limit) + end : value
}

export function getFirstWord(value: string) {
	return value.split(" ")[0]
}

export const getInitials = (name: string) => {
	const trimmedName = name.trim()

	if (trimmedName.length <= 2) return trimmedName

	return trimmedName
		.split(/\s+/)
		.map((w) => [...w][0])
		.slice(0, 2)
		.join("")
}

export const getGravatarUrl = (email: string, size?: number) => {
	const trimmedEmail = email.trim()
	if (!trimmedEmail) return ""
	const avatarSize = size || 50
	const emailMd5 = md5(trimmedEmail)
	return `https://www.gravatar.com/avatar/${emailMd5}?s=${String(Math.max(avatarSize, 250))}&d=identicon`
}

export function getServerSideErrors(errors: Errors & ErrorBag = {}) {
	return Object.entries(errors).reduce((acc: Record<string, { message: string }>, [key, value]) => {
		acc[key] = { message: value }
		return acc
	}, {})
}
