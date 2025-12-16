# Vite Build Tool Context

## Configuration

```typescript
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [],
  server: {
    proxy: { '/api': 'http://localhost:8000' }
  }
});
```

## Context7 Lookup

```python
mcp__context7__get-library-docs(
    context7CompatibleLibraryID="/vitejs/vite",
    topic="configuration plugins",
    mode="code"
)
```
