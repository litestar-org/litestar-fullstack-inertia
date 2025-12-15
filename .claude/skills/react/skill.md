# React + shadcn/ui Skill

## Quick Reference

### Component Pattern (This Project)

```tsx
import { Head } from '@inertiajs/react'
import AppLayout from '@/layouts/app-layout'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface Props {
  items: Item[]
}

export default function FeatureList({ items }: Props) {
  return (
    <AppLayout>
      <Head title="Feature List" />
      <div className="container mx-auto py-6">
        <Card>
          <CardHeader>
            <CardTitle>Features</CardTitle>
          </CardHeader>
          <CardContent>
            {items.map(item => (
              <div key={item.id}>{item.name}</div>
            ))}
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  )
}
```

### Layout Pattern

```tsx
// resources/layouts/app-layout.tsx
import { ReactNode } from 'react'
import Navbar from './partials/navbar'
import Footer from './partials/footer'

interface Props {
  children: ReactNode
}

export default function AppLayout({ children }: Props) {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-1">{children}</main>
      <Footer />
    </div>
  )
}
```

### shadcn/ui Components

Common components in `resources/components/ui/`:

```tsx
// Button
import { Button } from '@/components/ui/button'
<Button variant="default">Click me</Button>
<Button variant="outline">Outline</Button>
<Button variant="destructive">Delete</Button>

// Card
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
<Card>
  <CardHeader>
    <CardTitle>Title</CardTitle>
    <CardDescription>Description</CardDescription>
  </CardHeader>
  <CardContent>Content</CardContent>
</Card>

// Form components
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

// Dialog
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'

// Toast
import { useToast } from '@/components/ui/use-toast'
const { toast } = useToast()
toast({ title: "Success", description: "Item created" })
```

### Forms with Inertia + react-hook-form

```tsx
import { useForm } from '@inertiajs/react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import InputError from '@/components/input-error'

export default function CreateForm() {
  const { data, setData, post, processing, errors } = useForm({
    name: '',
    email: '',
  })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    post('/feature')
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <Label htmlFor="name">Name</Label>
        <Input
          id="name"
          value={data.name}
          onChange={e => setData('name', e.target.value)}
        />
        <InputError message={errors.name} />
      </div>

      <div>
        <Label htmlFor="email">Email</Label>
        <Input
          id="email"
          type="email"
          value={data.email}
          onChange={e => setData('email', e.target.value)}
        />
        <InputError message={errors.email} />
      </div>

      <Button type="submit" disabled={processing}>
        Create
      </Button>
    </form>
  )
}
```

### Tailwind CSS Patterns

```tsx
// Container
<div className="container mx-auto py-6">

// Grid
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">

// Flex
<div className="flex items-center justify-between">

// Card-like
<div className="rounded-lg border bg-card p-6 shadow-sm">

// Responsive text
<h1 className="text-2xl md:text-3xl font-bold">
```

### TypeScript Types

```tsx
// Define prop interfaces
interface Item {
  id: string
  name: string
  createdAt: string
}

interface Props {
  items: Item[]
  pagination?: {
    page: number
    total: number
  }
}

// Use with page component
export default function List({ items, pagination }: Props) {
  // ...
}
```

## Project Patterns

### File Organization
```
resources/
├── components/
│   ├── ui/          # shadcn/ui components
│   ├── logo.tsx     # App-specific components
│   └── theme-toggle.tsx
├── layouts/
│   ├── app-layout.tsx
│   ├── guest-layout.tsx
│   └── partials/
│       ├── navbar.tsx
│       └── footer.tsx
├── pages/
│   ├── dashboard.tsx
│   ├── auth/
│   │   ├── login.tsx
│   │   └── register.tsx
│   └── feature/
│       ├── list.tsx
│       └── show.tsx
└── main.tsx
```

### Path Aliases (tsconfig.json)
```json
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./resources/*"]
    }
  }
}
```

## Context7 Lookup

```python
mcp__context7__get-library-docs(
    context7CompatibleLibraryID="/facebook/react",
    topic="hooks",  # or: components, state
    mode="code"
)
```

## Related Files

- `resources/main.tsx` - Entry point
- `resources/components/ui/` - shadcn/ui components
- `resources/layouts/` - Layout components
- `components.json` - shadcn/ui configuration
- `tailwind.config.cjs` - Tailwind configuration
