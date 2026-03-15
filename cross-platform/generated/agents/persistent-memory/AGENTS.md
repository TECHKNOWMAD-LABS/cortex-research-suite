# persistent-memory

SQLite-backed persistent memory with FTS5 full-text search for cross-session knowledge retention.

## Tools

- **memory_operation**: Store, retrieve, or search persistent memory entries

## Integration

### MCP Server (Claude, Copilot, Cursor, Windsurf, VS Code, JetBrains)
```bash
cd mcp/persistent-memory && uv run python server.py
```

### LangChain / LangGraph
```python
from langchain.persistent_memory.tools import get_all_tools
tools = get_all_tools()
```

### CrewAI
```python
from crewai.persistent_memory.tools import *
```

### OpenAI Custom GPT
Import `openai/persistent-memory/openapi.json` as a GPT Action.

## License

MIT — TECHKNOWMAD LABS
