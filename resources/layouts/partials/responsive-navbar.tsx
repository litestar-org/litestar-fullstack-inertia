import { Link, router, usePage } from "@inertiajs/react"
import { ChevronDownIcon, CircleUserIcon, LogOutIcon, UserRoundCogIcon } from "lucide-react"
import { Logo } from "@/components/logo"
import { Avatar, AvatarImage } from "@/components/ui/avatar"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { route } from "@/lib/generated/routes"
import { getFirstWord, getGravatarUrl, strLimit } from "@/lib/utils"
import type { FullSharedProps } from "@/lib/generated/page-props"

const ResponsiveNavbar = () => {
	const { auth } = usePage<FullSharedProps>().props
	return (
		<nav className="block border-b px-4 py-2 sm:hidden">
			<div className="flex items-center justify-between py-1">
				<Link href="/">
					<Logo className="w-8 fill-red-600" />
				</Link>
				<div className="flex items-center gap-x-1">
					<DropdownMenu modal={false}>
						<DropdownMenuTrigger asChild className="focus:outline-none">
							<button type="button" className="flex items-center focus:outline-none">
								{auth?.user?.id ? getFirstWord(auth?.user.name ?? auth.user.email) : "Menu"}
								<ChevronDownIcon className="ml-2 size-4" />
							</button>
						</DropdownMenuTrigger>
						<DropdownMenuContent className="mr-8 w-72">
							{auth?.user && (
								<>
									<DropdownMenuLabel>
										<div className="flex items-center font-normal">
											<Avatar>
												<AvatarImage src={auth.user.avatarUrl ?? getGravatarUrl(auth.user.email)} alt={auth?.user.name ?? auth.user.email} />
											</Avatar>
											<div className="ml-3">
												<strong className="font-semibold text-primary">{auth.user.name}</strong>
												<div className="text-muted-foreground">{strLimit(auth.user.email, 28)}</div>
											</div>
										</div>
									</DropdownMenuLabel>
									<DropdownMenuSeparator />
								</>
							)}
							<DropdownMenuItem>
								<Link href={route("dashboard")}>Home</Link>
							</DropdownMenuItem>
							<DropdownMenuItem>
								<Link href={route("about")}>About</Link>
							</DropdownMenuItem>
							{auth?.user ? (
								<>
									<DropdownMenuSeparator />
									<DropdownMenuItem>
										<Link href={route("dashboard")}>Dashboard</Link>
									</DropdownMenuItem>
									<DropdownMenuItem className="flex items-center justify-between">
										<Link className="flex items-center" href={route("profile.show")}>
											<UserRoundCogIcon className="mr-2 size-4" />
											Profile
										</Link>
									</DropdownMenuItem>
									<DropdownMenuSeparator />
									<DropdownMenuItem onClick={() => router.post(route("logout"))}>
										<span>Logout</span>
									</DropdownMenuItem>
								</>
							) : (
								<>
									<DropdownMenuSeparator />
									<DropdownMenuItem asChild>
										<Link className="flex items-center" href={route("login")}>
											<LogOutIcon className="mr-2 size-4 rotate-180" />
											<span>Login</span>
										</Link>
									</DropdownMenuItem>
									<DropdownMenuItem asChild>
										<Link className="flex items-center" href={route("register")}>
											<CircleUserIcon className="mr-2 size-4" />
											<span>Register</span>
										</Link>
									</DropdownMenuItem>
								</>
							)}
						</DropdownMenuContent>
					</DropdownMenu>
				</div>
			</div>
		</nav>
	)
}

export default ResponsiveNavbar
