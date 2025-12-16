import type { ErrorBag, Errors, Page, PageProps } from "@inertiajs/core"
import type { AxiosInstance } from "axios"
import type { AuthData, CurrentTeam, FlashMessages } from "."

declare global {
	interface Window {
		axios: AxiosInstance
	}

	/**
	 * Inertia page props - core props available on all pages.
	 * Includes auth, flash messages, errors, and CSRF token.
	 */
	interface InertiaProps extends Page<PageProps> {
		flash: FlashMessages
		errors: Errors & ErrorBag
		csrf_token: string
		auth?: AuthData
		currentTeam?: CurrentTeam
		// Static config props from ViteConfig.inertia.extra_static_page_props
		canResetPassword?: boolean
		hasTermsAndPrivacyPolicyFeature?: boolean
		mustVerifyEmail?: boolean
		githubOAuthEnabled?: boolean
		googleOAuthEnabled?: boolean
		registrationEnabled?: boolean
		mfaEnabled?: boolean
	}
}
