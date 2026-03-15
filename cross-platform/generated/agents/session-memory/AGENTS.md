# session-memory

Session-scoped memory persistence across conversations with automatic context restoration.

## Tools

- **session_operation**: Store or retrieve session-scoped memory

## Integration

### MCP Server (Claude, Copilot, Cursor, Windsurf, VS Code, JetBrains)
```bash
cd mcp/session-memory && uv run python server.py
```

### LangChain / LangGraph
```python
from langchain.session_memory.tools import get_all_tools
tools = get_all_tools()
```

### CrewAI
```python
from crewai.session_memory.tools import *
```

### OpenAI Custom GPT
Import `openai/session-memory/openapi.json` as a GPT Action.

## License

MIT — TECHKNOWMAD LABS
