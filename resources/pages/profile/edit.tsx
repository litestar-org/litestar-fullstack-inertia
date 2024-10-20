import { Container } from "@/components/container"
import { Header } from "@/components/header"
import { AppLayout } from "@/layouts/app-layout"
import DeleteUserForm from "@/pages/profile/partials/delete-user-form"
import UpdatePasswordForm from "@/pages/profile/partials/update-password-form"
import UpdateProfileInformationForm from "@/pages/profile/partials/update-profile-information-form"
import { Head } from "@inertiajs/react"

interface Props {
	mustVerifyEmail: boolean
	status?: string
}

const title = "User Profile"
export default function Edit({ mustVerifyEmail, status }: Props) {
	return (
		<>
			<Head title={title} />
			<Header title={title} />
			<Container>
				<div className="max-w-3xl space-y-6">
					<UpdateProfileInformationForm mustVerifyEmail={mustVerifyEmail} status={status} />
					<UpdatePasswordForm />
					<DeleteUserForm />
				</div>
			</Container>
		</>
	)
}

Edit.layout = (page: any) => <AppLayout children={page} />
