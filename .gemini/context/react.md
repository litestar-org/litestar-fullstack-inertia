# React Framework Context

Expert knowledge for React 18+ with TypeScript.

## Component Patterns

```tsx
export function ItemList({ items }: Props) {
  const [selected, setSelected] = useState<Item | null>(null);
  return (
    <ul>
      {items.map(item => (
        <li key={item.id}>{item.name}</li>
      ))}
    </ul>
  );
}
```

## Context7 Lookup

```python
mcp__context7__get-library-docs(
    context7CompatibleLibraryID="/facebook/react",
    topic="hooks components",
    mode="code"
)
```
