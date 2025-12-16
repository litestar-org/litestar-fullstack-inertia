# Vue 3 Framework Context

Expert knowledge for Vue 3 Composition API.

## Component Pattern

```vue
<script setup lang="ts">
import { ref, computed } from 'vue';

const items = ref<Item[]>([]);
const filtered = computed(() => items.value.filter(i => i.active));
</script>

<template>
  <ul>
    <li v-for="item in filtered" :key="item.id">{{ item.name }}</li>
  </ul>
</template>
```

## Context7 Lookup

```python
mcp__context7__get-library-docs(
    context7CompatibleLibraryID="/vuejs/core",
    topic="composition-api",
    mode="code"
)
```
