import { createInertiaApp } from "@inertiajs/react"
import axios from "axios"
import { resolvePageComponent } from "litestar-vite-plugin/inertia-helpers"
import { createRoot, hydrateRoot } from "react-dom/client"
import { ThemeProvider } from "@/components/theme-provider"
import "./main.css"

const appName = import.meta.env.VITE_APP_NAME || "Fullstack"
axios.defaults.withCredentials = true

createInertiaApp({
	title: (title: string) => `${title} - ${appName}`,
	// defaults: {
	//     future: {
	//         useScriptElementForInitialPage: true,
	//     },
	// },
	resolve: (name: string) => resolvePageComponent(`./pages/${name}.tsx`, import.meta.glob("./pages/**/*.tsx")),
	setup({ el, App, props }: { el: HTMLElement; App: React.ComponentType; props: Record<string, unknown> }) {
		const appElement = (
			<ThemeProvider defaultTheme="system" storageKey="ui-theme">
				<App {...props} />
			</ThemeProvider>
		)
		if (import.meta.env.DEV) {
			createRoot(el).render(appElement)
			return
		}

		hydrateRoot(el, appElement)
	},
	progress: {
		color: "#EDB641",
	},
} as unknown as Parameters<typeof createInertiaApp>[0])
