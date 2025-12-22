/**
 * User-defined type extensions for Inertia page props.
 * This file is generated ONCE and never overwritten - edit freely!
 *
 * Add properties to these interfaces to extend the generated types.
 * The main page-props.ts file imports and uses these extensions.
 */

import type { CurrentTeam } from "./api/types.gen"

/**
 * Extend the User interface with additional properties.
 */
export interface UserExtensions {
  avatarUrl?: string | null
  isVerified?: boolean
  teams: CurrentTeam[]
}

/**
 * Extend SharedProps with session-based or dynamic properties.
 */
export interface SharedPropsExtensions {
  // Add your custom shared props here
}
