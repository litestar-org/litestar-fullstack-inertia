import type { ErrorBag, Errors, Page, PageProps } from "@inertiajs/core"
import type { AxiosInstance } from "axios"
import type { AuthData, CurrentTeam, FlashMessages } from "."
declare global {
	interface Window {
		axios: AxiosInstance
	}

	interface InertiaProps extends Page<PageProps> {
		flash: FlashMessages
		errors: Errors & ErrorBag
		csrf_token: string
		auth?: AuthData
		currentTeam?: CurrentTeam
		[key: string]: any
	}
}
