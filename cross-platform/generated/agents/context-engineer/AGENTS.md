# context-engineer

Context window optimization and prompt context management for efficient LLM usage.

## Tools

- **optimize_context**: Optimize context window by prioritizing and compressing relevant content

## Integration

### MCP Server (Claude, Copilot, Cursor, Windsurf, VS Code, JetBrains)
```bash
cd mcp/context-engineer && uv run python server.py
```

### LangChain / LangGraph
```python
from langchain.context_engineer.tools import get_all_tools
tools = get_all_tools()
```

### CrewAI
```python
from crewai.context_engineer.tools import *
```

### OpenAI Custom GPT
Import `openai/context-engineer/openapi.json` as a GPT Action.

## License

MIT — TECHKNOWMAD LABS
