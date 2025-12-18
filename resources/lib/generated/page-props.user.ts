/**
 * User-defined type overrides for Inertia page props.
 * This file is generated ONCE and never overwritten - edit freely!
 *
 * Use module augmentation to extend generated types.
 *
 * IMPORTANT: If you see "module 'litestar-vite-plugin/inertia' cannot be found":
 * 1. Ensure litestar-vite-plugin is installed: npm install litestar-vite-plugin
 * 2. Make sure your tsconfig.json has "moduleResolution": "bundler" or "node16"
 */

// Reference the base types to enable module augmentation
/// <reference types="litestar-vite-plugin/inertia" />

declare module "litestar-vite-plugin/inertia" {
  // Example: Add fields to the User interface
  // interface User {
  //   avatarUrl?: string | null
  //   roles: string[]
  //   teams: Team[]
  // }

  // Example: Add session-based shared props
  // interface SharedProps {
  //   currentTeam?: {
  //     teamId: string
  //     teamName: string
  //   }
  //   locale?: string
  // }
}

// Export custom types that can be used in page props
// export interface CurrentTeam {
//   teamId: string
//   teamName: string
// }

export {}
