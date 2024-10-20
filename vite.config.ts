import path from "path"
import react from "@vitejs/plugin-react"
import litestar from "litestar-vite-plugin"
import { defineConfig } from "vite"

const ASSET_URL = process.env.ASSET_URL || "/static/"
const VITE_PORT = process.env.VITE_PORT || "5173"
const VITE_HOST = process.env.VITE_HOST || "localhost"
export default defineConfig({
	base: `${ASSET_URL}`,
	clearScreen: false,
	publicDir: "public/",
	server: {
		host: "0.0.0.0",
		port: +`${VITE_PORT}`,
		cors: true,
		hmr: {
			host: `${VITE_HOST}`,
		},
	},
	plugins: [
		react(),
		litestar({
			input: ["resources/main.tsx", "resources/main.css"],
			assetUrl: `${ASSET_URL}`,
			bundleDirectory: "app/domain/web/public",
			resourceDirectory: "resources",
			hotFile: "app/domain/web/public/hot",
		}),
	],
	resolve: {
		alias: {
			"@": path.resolve(__dirname, "resources"),
		},
	},
})
