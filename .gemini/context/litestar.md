# Litestar Framework Context

Expert knowledge for Litestar Python web framework.

## Plugin Development

```python
from litestar.plugins import InitPluginProtocol

class MyPlugin(InitPluginProtocol):
    def on_app_init(self, app_config: AppConfig) -> AppConfig:
        return app_config
```

## Route Handlers

```python
from litestar import get, post

@get("/items/{item_id:int}")
async def get_item(item_id: int) -> Item:
    return await fetch_item(item_id)
```

## Context7 Lookup

```python
mcp__context7__get-library-docs(
    context7CompatibleLibraryID="/litestar-org/litestar",
    topic="plugins middleware",
    mode="code"
)
```
