import * as ToastPrimitives from "@radix-ui/react-toast"
import { cva, type VariantProps } from "class-variance-authority"
import { X } from "lucide-react"
import * as React from "react"

import { cn } from "@/lib/utils"

const ToastProvider = ToastPrimitives.Provider

const ToastViewport = React.forwardRef<React.ElementRef<typeof ToastPrimitives.Viewport>, React.ComponentPropsWithoutRef<typeof ToastPrimitives.Viewport>>(
	({ className, ...props }, ref) => (
		<ToastPrimitives.Viewport
			ref={ref}
			className={cn("fixed top-0 z-[100] flex max-h-screen w-full flex-col-reverse p-4 sm:top-auto sm:right-0 sm:bottom-0 sm:flex-col md:max-w-[420px]", className)}
			{...props}
		/>
	),
)
ToastViewport.displayName = ToastPrimitives.Viewport.displayName

const toastVariants = cva(
	"group pointer-events-auto relative flex w-full items-center justify-between space-x-4 overflow-hidden rounded-md border p-6 pr-8 shadow-lg transition-all data-[swipe=cancel]:translate-x-0 data-[swipe=end]:translate-x-[var(--radix-toast-swipe-end-x)] data-[swipe=move]:translate-x-[var(--radix-toast-swipe-move-x)] data-[swipe=move]:transition-none data-[state=open]:animate-in data-[state=closed]:animate-out data-[swipe=end]:animate-out data-[state=closed]:fade-out-80 data-[state=closed]:slide-out-to-right-full data-[state=open]:slide-in-from-top-full data-[state=open]:sm:slide-in-from-bottom-full",
	{
		variants: {
			variant: {
				default: "border-primary/40 bg-[#FFF4D6] text-[#202235] dark:border-primary/40 dark:bg-[#202235] dark:text-white",
				success: "success group border-green-200 bg-green-50 text-green-900 dark:border-green-800/40 dark:bg-green-950 dark:text-green-100",
				warning: "warning group border-amber-200 bg-amber-50 text-amber-900 dark:border-amber-800/40 dark:bg-amber-950 dark:text-amber-100",
				destructive: "destructive group border-red-200 bg-red-50 text-red-900 dark:border-red-800/40 dark:bg-red-950 dark:text-red-100",
			},
		},
		defaultVariants: {
			variant: "default",
		},
	},
)

const Toast = React.forwardRef<React.ElementRef<typeof ToastPrimitives.Root>, React.ComponentPropsWithoutRef<typeof ToastPrimitives.Root> & VariantProps<typeof toastVariants>>(
	({ className, variant, ...props }, ref) => {
		return <ToastPrimitives.Root ref={ref} className={cn(toastVariants({ variant }), className)} {...props} />
	},
)
Toast.displayName = ToastPrimitives.Root.displayName

const ToastAction = React.forwardRef<React.ElementRef<typeof ToastPrimitives.Action>, React.ComponentPropsWithoutRef<typeof ToastPrimitives.Action>>(
	({ className, ...props }, ref) => (
		<ToastPrimitives.Action
			ref={ref}
			className={cn(
				"inline-flex h-8 shrink-0 items-center justify-center rounded-md border bg-transparent px-3 font-medium text-sm ring-offset-background transition-colors hover:bg-secondary focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 group-[.success]:border-green-200 group-[.success]:text-green-900 group-[.success]:hover:border-green-300 group-[.success]:hover:bg-green-100 group-[.success]:focus:ring-green-400 dark:group-[.success]:border-green-800/40 dark:group-[.success]:text-green-100 dark:group-[.success]:hover:bg-green-900/30 group-[.warning]:border-amber-200 group-[.warning]:text-amber-900 group-[.warning]:hover:border-amber-300 group-[.warning]:hover:bg-amber-100 group-[.warning]:focus:ring-amber-400 dark:group-[.warning]:border-amber-800/40 dark:group-[.warning]:text-amber-100 dark:group-[.warning]:hover:bg-amber-900/30 group-[.destructive]:border-red-200 group-[.destructive]:text-red-900 group-[.destructive]:hover:border-red-300 group-[.destructive]:hover:bg-red-100 group-[.destructive]:focus:ring-red-400 dark:group-[.destructive]:border-red-800/40 dark:group-[.destructive]:text-red-100 dark:group-[.destructive]:hover:bg-red-900/30",
				className,
			)}
			{...props}
		/>
	),
)
ToastAction.displayName = ToastPrimitives.Action.displayName

const ToastClose = React.forwardRef<React.ElementRef<typeof ToastPrimitives.Close>, React.ComponentPropsWithoutRef<typeof ToastPrimitives.Close>>(
	({ className, ...props }, ref) => (
		<ToastPrimitives.Close
			ref={ref}
			className={cn(
				"absolute top-2 right-2 rounded-md p-1 text-foreground/50 opacity-0 transition-opacity hover:text-foreground focus:opacity-100 focus:outline-none focus:ring-2 group-hover:opacity-100 group-[.success]:text-green-700 group-[.success]:focus:ring-green-400 group-[.success]:hover:text-green-900 dark:group-[.success]:text-green-200 dark:group-[.success]:hover:text-green-100 group-[.warning]:text-amber-700 group-[.warning]:focus:ring-amber-400 group-[.warning]:hover:text-amber-900 dark:group-[.warning]:text-amber-200 dark:group-[.warning]:hover:text-amber-100 group-[.destructive]:text-red-700 group-[.destructive]:focus:ring-red-400 group-[.destructive]:hover:text-red-900 dark:group-[.destructive]:text-red-200 dark:group-[.destructive]:hover:text-red-100",
				className,
			)}
			toast-close=""
			{...props}
		>
			<X className="h-4 w-4" />
		</ToastPrimitives.Close>
	),
)
ToastClose.displayName = ToastPrimitives.Close.displayName

const ToastTitle = React.forwardRef<React.ElementRef<typeof ToastPrimitives.Title>, React.ComponentPropsWithoutRef<typeof ToastPrimitives.Title>>(
	({ className, ...props }, ref) => <ToastPrimitives.Title ref={ref} className={cn("text-sm font-semibold text-current", className)} {...props} />,
)
ToastTitle.displayName = ToastPrimitives.Title.displayName

const ToastDescription = React.forwardRef<React.ElementRef<typeof ToastPrimitives.Description>, React.ComponentPropsWithoutRef<typeof ToastPrimitives.Description>>(
	({ className, ...props }, ref) => <ToastPrimitives.Description ref={ref} className={cn("text-sm text-current/90", className)} {...props} />,
)
ToastDescription.displayName = ToastPrimitives.Description.displayName

type ToastProps = React.ComponentPropsWithoutRef<typeof Toast>

type ToastActionElement = React.ReactElement<typeof ToastAction>

export { type ToastProps, type ToastActionElement, ToastProvider, ToastViewport, Toast, ToastTitle, ToastDescription, ToastClose, ToastAction }
