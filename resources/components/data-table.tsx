import { router } from "@inertiajs/react"
import { ArrowDown, ArrowUp, ArrowUpDown, ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight, Search } from "lucide-react"
import * as React from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"

export interface Column<T> {
	key: keyof T | string
	label: string
	sortable?: boolean
	render?: (row: T) => React.ReactNode
}

interface DataTableProps<T> {
	data: T[]
	columns: Column<T>[]
	total: number
	pageSize?: number
	currentPage?: number
	searchPlaceholder?: string
	routeName: string
	routeParams?: Record<string, unknown>
	sortField?: string
	sortOrder?: "asc" | "desc"
	searchQuery?: string
	emptyMessage?: string
}

export function DataTable<T extends { id: string | number }>({
	data,
	columns,
	total,
	pageSize = 25,
	currentPage = 1,
	searchPlaceholder = "Search...",
	routeName,
	routeParams = {},
	sortField,
	sortOrder = "desc",
	searchQuery = "",
	emptyMessage = "No results found.",
}: DataTableProps<T>) {
	const [localSearch, setLocalSearch] = React.useState(searchQuery)
	const totalPages = Math.ceil(total / pageSize)

	const navigateWithParams = React.useCallback(
		(newParams: Record<string, unknown>) => {
			router.get(
				routeName,
				{
					...routeParams,
					searchString: localSearch || undefined,
					orderBy: sortField,
					sortOrder,
					currentPage,
					pageSize,
					...newParams,
				},
				{ preserveState: true, preserveScroll: true },
			)
		},
		[routeName, routeParams, localSearch, sortField, sortOrder, currentPage, pageSize],
	)

	const handleSearch = React.useCallback(
		(e: React.FormEvent) => {
			e.preventDefault()
			navigateWithParams({ searchString: localSearch || undefined, currentPage: 1 })
		},
		[localSearch, navigateWithParams],
	)

	const handleSort = (key: string) => {
		const newOrder = sortField === key && sortOrder === "asc" ? "desc" : "asc"
		navigateWithParams({ orderBy: key, sortOrder: newOrder })
	}

	const handlePageChange = (newPage: number) => {
		navigateWithParams({ currentPage: newPage })
	}

	const handlePageSizeChange = (newSize: string) => {
		navigateWithParams({ pageSize: Number(newSize), currentPage: 1 })
	}

	return (
		<div className="space-y-4">
			{/* Search and Controls */}
			<div className="flex items-center justify-between gap-4">
				<form onSubmit={handleSearch} className="flex items-center gap-2">
					<div className="relative">
						<Search className="-translate-y-1/2 absolute top-1/2 left-3 h-4 w-4 text-muted-foreground" />
						<Input placeholder={searchPlaceholder} value={localSearch} onChange={(e) => setLocalSearch(e.target.value)} className="w-64 pl-9" />
					</div>
					<Button type="submit" variant="secondary" size="sm">
						Search
					</Button>
				</form>

				<div className="flex items-center gap-2">
					<span className="text-muted-foreground text-sm">{total} total</span>
				</div>
			</div>

			{/* Table */}
			<div className="rounded-md border">
				<Table>
					<TableHeader>
						<TableRow>
							{columns.map((column) => (
								<TableHead key={String(column.key)}>
									{column.sortable ? (
										<button type="button" className="flex items-center gap-1 hover:text-foreground" onClick={() => handleSort(String(column.key))}>
											{column.label}
											{sortField === column.key ? (
												sortOrder === "asc" ? (
													<ArrowUp className="h-4 w-4" />
												) : (
													<ArrowDown className="h-4 w-4" />
												)
											) : (
												<ArrowUpDown className="h-4 w-4 opacity-50" />
											)}
										</button>
									) : (
										column.label
									)}
								</TableHead>
							))}
						</TableRow>
					</TableHeader>
					<TableBody>
						{data.length === 0 ? (
							<TableRow>
								<TableCell colSpan={columns.length} className="h-24 text-center">
									{emptyMessage}
								</TableCell>
							</TableRow>
						) : (
							data.map((row) => (
								<TableRow key={row.id}>
									{columns.map((column) => (
										<TableCell key={String(column.key)}>{column.render ? column.render(row) : String((row as Record<string, unknown>)[column.key as string] ?? "")}</TableCell>
									))}
								</TableRow>
							))
						)}
					</TableBody>
				</Table>
			</div>

			{/* Pagination */}
			<div className="flex items-center justify-between">
				<div className="flex items-center gap-2">
					<span className="text-muted-foreground text-sm">Rows per page</span>
					<Select value={String(pageSize)} onValueChange={handlePageSizeChange}>
						<SelectTrigger className="w-20">
							<SelectValue />
						</SelectTrigger>
						<SelectContent>
							<SelectItem value="10">10</SelectItem>
							<SelectItem value="25">25</SelectItem>
							<SelectItem value="50">50</SelectItem>
							<SelectItem value="100">100</SelectItem>
						</SelectContent>
					</Select>
				</div>

				<div className="flex items-center gap-2">
					<span className="text-muted-foreground text-sm">
						Page {currentPage} of {totalPages || 1}
					</span>
					<div className="flex items-center gap-1">
						<Button variant="outline" size="icon" onClick={() => handlePageChange(1)} disabled={currentPage <= 1}>
							<ChevronsLeft className="h-4 w-4" />
						</Button>
						<Button variant="outline" size="icon" onClick={() => handlePageChange(currentPage - 1)} disabled={currentPage <= 1}>
							<ChevronLeft className="h-4 w-4" />
						</Button>
						<Button variant="outline" size="icon" onClick={() => handlePageChange(currentPage + 1)} disabled={currentPage >= totalPages}>
							<ChevronRight className="h-4 w-4" />
						</Button>
						<Button variant="outline" size="icon" onClick={() => handlePageChange(totalPages)} disabled={currentPage >= totalPages}>
							<ChevronsRight className="h-4 w-4" />
						</Button>
					</div>
				</div>
			</div>
		</div>
	)
}
