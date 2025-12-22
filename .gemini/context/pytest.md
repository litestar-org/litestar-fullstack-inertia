# pytest Testing Context

## Basic Tests (Function-Based Only)

```python
def test_addition():
    assert 1 + 1 == 2

@pytest.fixture
def sample_data():
    return {"key": "value"}

@pytest.mark.asyncio
async def test_async():
    result = await async_op()
    assert result is not None
```

## Context7 Lookup

```python
mcp__context7__get-library-docs(
    context7CompatibleLibraryID="/pytest-dev/pytest",
    topic="fixtures async",
    mode="code"
)
```
