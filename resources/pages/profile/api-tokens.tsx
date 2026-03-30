import { Head } from "@inertiajs/react"
import { Container } from "@/components/container"
import { Header } from "@/components/header"
import { AppLayout } from "@/layouts/app-layout"
import ApiTokenManager from "@/pages/profile/partials/api-token-manager"

export interface ApiTokenAbility {
	value: string
	label: string
	description: string
}

export interface ApiTokenItem {
	id: string
	name: string
	abilities: string[]
	createdAt: string
	lastUsedAt?: string | null
	expiresAt?: string | null
}

interface ApiTokensPageProps {
	tokens: ApiTokenItem[]
	availableAbilities: ApiTokenAbility[]
	defaultAbilities: string[]
}

export default function ApiTokensPage({ tokens, availableAbilities, defaultAbilities }: ApiTokensPageProps) {
	return (
		<>
			<Head title="API Tokens" />
			<Header title="API Tokens" />
			<Container>
				<ApiTokenManager tokens={tokens} availableAbilities={availableAbilities} defaultAbilities={defaultAbilities} />
			</Container>
		</>
	)
}

ApiTokensPage.layout = (page: React.ReactNode) => <AppLayout>{page}</AppLayout>
