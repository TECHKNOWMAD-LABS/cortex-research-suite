# diff-generator

Structured diff generation for code and document changes with context-aware formatting.

## Tools

- **generate_diff**: Generate structured diff between two versions of content

## Integration

### MCP Server (Claude, Copilot, Cursor, Windsurf, VS Code, JetBrains)
```bash
cd mcp/diff-generator && uv run python server.py
```

### LangChain / LangGraph
```python
from langchain.diff_generator.tools import get_all_tools
tools = get_all_tools()
```

### CrewAI
```python
from crewai.diff_generator.tools import *
```

### OpenAI Custom GPT
Import `openai/diff-generator/openapi.json` as a GPT Action.

## License

MIT — TECHKNOWMAD LABS