# dev-lifecycle-engine

Development lifecycle management covering planning, implementation, testing, and deployment phases.

## Tools

- **manage_lifecycle**: Execute development lifecycle phase with automated tracking

## Integration

### MCP Server (Claude, Copilot, Cursor, Windsurf, VS Code, JetBrains)
```bash
cd mcp/dev-lifecycle-engine && uv run python server.py
```

### LangChain / LangGraph
```python
from langchain.dev_lifecycle_engine.tools import get_all_tools
tools = get_all_tools()
```

### CrewAI
```python
from crewai.dev_lifecycle_engine.tools import *
```

### OpenAI Custom GPT
Import `openai/dev-lifecycle-engine/openapi.json` as a GPT Action.

## License

MIT — TECHKNOWMAD LABS
