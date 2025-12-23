import { Head } from "@inertiajs/react"
import { ImageIcon, KeyRound, Link2, Shield, Trash2, User } from "lucide-react"
import { useState } from "react"
import { Container } from "@/components/container"
import { Header } from "@/components/header"
import { SettingsSidebar, type SettingsSidebarItem } from "@/components/settings-sidebar"
import { AppLayout } from "@/layouts/app-layout"
import AvatarForm from "@/pages/profile/partials/avatar-form"
import ConnectedAccountsForm from "@/pages/profile/partials/connected-accounts-form"
import DeleteUserForm from "@/pages/profile/partials/delete-user-form"
import MfaForm from "@/pages/profile/partials/mfa-form"
import UpdatePasswordForm from "@/pages/profile/partials/update-password-form"
import UpdateProfileInformationForm from "@/pages/profile/partials/update-profile-information-form"

interface Props {
	mustVerifyEmail: boolean
	status?: string
}

const sidebarItems: SettingsSidebarItem[] = [
	{
		id: "avatar",
		label: "Avatar",
		icon: ImageIcon,
		description: "Upload a profile picture",
	},
	{
		id: "profile-information",
		label: "Profile Information",
		icon: User,
		description: "Update your name and email",
	},
	{
		id: "update-password",
		label: "Password",
		icon: KeyRound,
		description: "Change your password",
	},
	{
		id: "mfa",
		label: "MFA",
		icon: Shield,
		description: "Secure your account with MFA",
	},
	{
		id: "connected-accounts",
		label: "Connected Accounts",
		icon: Link2,
		description: "Manage OAuth providers",
	},
	{
		id: "delete-account",
		label: "Delete Account",
		icon: Trash2,
		description: "Permanently delete your account",
	},
]

const title = "User Profile"
export default function Edit({ mustVerifyEmail, status }: Props) {
	const [activeSection, setActiveSection] = useState("avatar")

	return (
		<>
			<Head title={title} />
			<Header title={title} />
			<Container>
				<div className="grid gap-6 lg:grid-cols-3">
					{/* Main Content */}
					<div className="lg:col-span-2 space-y-6">
						<div id="avatar">
							<AvatarForm />
						</div>
						<div id="profile-information">
							<UpdateProfileInformationForm mustVerifyEmail={mustVerifyEmail} status={status} />
						</div>
						<div id="update-password">
							<UpdatePasswordForm />
						</div>
						<div id="mfa">
							<MfaForm />
						</div>
						<div id="connected-accounts">
							<ConnectedAccountsForm />
						</div>
						<div id="delete-account">
							<DeleteUserForm />
						</div>
					</div>

					{/* Sidebar */}
					<div className="space-y-6">
						<SettingsSidebar title="Settings" items={sidebarItems} activeId={activeSection} onItemClick={setActiveSection} />
					</div>
				</div>
			</Container>
		</>
	)
}

Edit.layout = (page: React.ReactNode) => <AppLayout>{page}</AppLayout>
