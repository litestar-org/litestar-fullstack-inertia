/**
 * User-defined type extensions for Inertia page props.
 * This file is generated ONCE and never overwritten - edit freely!
 *
 * Add properties to these interfaces to extend the generated types.
 * The main page-props.ts file imports and uses these extensions.
 */

/**
 * Extend the User interface with additional properties.
 *
 * @example
 * export interface UserExtensions {
 *   avatarUrl?: string | null
 *   roles: string[]
 *   teams: Team[]
 * }
 */
export interface UserExtensions {
  avatarUrl?: string | null
}

/**
 * Extend SharedProps with session-based or dynamic properties.
 *
 * @example
 * export interface SharedPropsExtensions {
 *   locale?: string
 *   currentTeam?: {
 *     teamId: string
 *     teamName: string
 *   }
 * }
 */
export interface SharedPropsExtensions {
  // Add your custom shared props here
}

// Export custom types that can be used in page props
// export interface CurrentTeam {
//   teamId: string
//   teamName: string
// }
