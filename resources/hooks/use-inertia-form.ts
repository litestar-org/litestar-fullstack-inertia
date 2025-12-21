import { zodResolver } from "@hookform/resolvers/zod"
import { router } from "@inertiajs/react"
import { useCallback, useState } from "react"
import { type DefaultValues, type FieldValues, type Path, type UseFormReturn, useForm } from "react-hook-form"
import type { z } from "zod"

type HttpMethod = "post" | "put" | "patch" | "delete"

interface UseInertiaFormOptions<TSchema extends z.ZodType, TSubmit = z.infer<TSchema>> {
	/** Zod schema for validation */
	schema: TSchema
	/** Default form values */
	defaultValues: DefaultValues<z.infer<TSchema>>
	/** URL to submit to (use route() helper) */
	url: string
	/** HTTP method for submission */
	method?: HttpMethod
	/** Transform form values before submission (e.g., to omit confirmation fields) */
	transform?: (values: z.infer<TSchema>) => TSubmit
	/** Callback on successful submission */
	onSuccess?: () => void
	/** Callback on error (receives error object) */
	onError?: (errors: Record<string, string>) => void
	/** Callback when submission finishes (success or error) */
	onFinish?: () => void
	/** Preserve scroll position on submission */
	preserveScroll?: boolean
	/** Preserve form state on submission */
	preserveState?: boolean
}

interface UseInertiaFormReturn<TSchema extends z.ZodType> {
	/** react-hook-form instance */
	form: UseFormReturn<z.infer<TSchema>>
	/** Whether form is currently submitting */
	isSubmitting: boolean
	/** Submit handler to pass to form onSubmit */
	handleSubmit: (e?: React.BaseSyntheticEvent) => Promise<void>
	/** Reset form to default values */
	reset: () => void
}

/**
 * Hook that combines Zod validation with Inertia form submission.
 *
 * @example
 * const loginSchema = z.object({
 *   email: z.string().email(),
 *   password: z.string().min(6),
 * })
 *
 * function LoginForm() {
 *   const { form, isSubmitting, handleSubmit } = useInertiaForm({
 *     schema: loginSchema,
 *     defaultValues: { email: "", password: "" },
 *     url: route("login"),
 *     onSuccess: () => toast.success("Logged in!"),
 *   })
 *
 *   return (
 *     <Form {...form}>
 *       <form onSubmit={handleSubmit}>
 *         <FormField control={form.control} name="email" ... />
 *         <FormField control={form.control} name="password" ... />
 *         <Button type="submit" disabled={isSubmitting}>
 *           {isSubmitting ? "Signing in..." : "Sign In"}
 *         </Button>
 *       </form>
 *     </Form>
 *   )
 * }
 */
export function useInertiaForm<TSchema extends z.ZodType, TSubmit = z.infer<TSchema>>({
	schema,
	defaultValues,
	url,
	method = "post",
	transform,
	onSuccess,
	onError,
	onFinish,
	preserveScroll = true,
	preserveState = false,
}: UseInertiaFormOptions<TSchema, TSubmit>): UseInertiaFormReturn<TSchema> {
	type FormData = z.infer<TSchema>

	const [isSubmitting, setIsSubmitting] = useState(false)

	const form = useForm<FormData>({
		resolver: zodResolver(schema),
		defaultValues,
	})

	const handleSubmit = useCallback(
		async (e?: React.BaseSyntheticEvent) => {
			// Prevent default form submission
			e?.preventDefault()

			// Validate with react-hook-form (which uses Zod)
			const isValid = await form.trigger()
			if (!isValid) return

			const values = form.getValues()
			const submitValues = transform ? transform(values) : values
			setIsSubmitting(true)

			const routerMethod = router[method] as typeof router.post

			routerMethod(url, submitValues as FieldValues, {
				preserveScroll,
				preserveState,
				onSuccess: () => {
					onSuccess?.()
				},
				onError: (errors) => {
					// Map server errors to form fields
					for (const [field, message] of Object.entries(errors)) {
						if (typeof message === "string") {
							// Check if field exists in schema
							const fieldPath = field as Path<FormData>
							if (field in defaultValues) {
								form.setError(fieldPath, { message })
							} else {
								// Set as root error if field not in form
								form.setError("root", { message })
							}
						}
					}
					onError?.(errors as Record<string, string>)
				},
				onFinish: () => {
					setIsSubmitting(false)
					onFinish?.()
				},
			})
		},
		[form, url, method, transform, defaultValues, preserveScroll, preserveState, onSuccess, onError, onFinish],
	)

	const reset = useCallback(() => {
		form.reset(defaultValues)
	}, [form, defaultValues])

	return {
		form,
		isSubmitting,
		handleSubmit,
		reset,
	}
}
