import { dirname } from "path"
import { fileURLToPath } from "url"

/** @type {import('next').NextConfig} */
const nextConfig = {
	turbopack: {
		root: dirname(fileURLToPath(import.meta.url)),
	},
	images: {
		remotePatterns: [
			{
				protocol: "https",
				hostname: "i.postimg.cc",
			},
		],
	},
}

export default nextConfig
