import { cn } from "@/lib/utils"

interface RetroGridProps {
	className?: string
	angle?: number
}

export function RetroGrid({ className, angle = 65 }: RetroGridProps) {
	return (
		<div
			className={cn("pointer-events-none absolute inset-0 overflow-hidden opacity-50 [perspective:200px]", className)}
			style={{ "--grid-angle": `${angle}deg` } as React.CSSProperties}
		>
			{/* Grid */}
			<div className="absolute inset-0 [transform:rotateX(var(--grid-angle))]">
				<div
					className={cn(
						"animate-grid",
						"[background-repeat:repeat] [background-size:60px_60px] [height:300vh] [inset:0%_0px] [margin-left:-50%] [transform-origin:100%_0_0] [width:600vw]",
						// Light mode grid
						"[background-image:linear-gradient(to_right,rgba(0,0,0,0.3)_1px,transparent_0),linear-gradient(to_bottom,rgba(0,0,0,0.3)_1px,transparent_0)]",
						// Dark mode grid
						"dark:[background-image:linear-gradient(to_right,rgba(255,255,255,0.2)_1px,transparent_0),linear-gradient(to_bottom,rgba(255,255,255,0.2)_1px,transparent_0)]",
					)}
				/>
			</div>

			{/* Gradient overlay */}
			<div className="absolute inset-0 bg-gradient-to-t from-background to-transparent to-90%" />
		</div>
	)
}
