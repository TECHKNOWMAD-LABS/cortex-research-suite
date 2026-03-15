# tdd-enforcer

Test-driven development enforcement with coverage tracking, test-first workflow validation, and red-green-refactor cycle monitoring.

## Tools

- **enforce_tdd**: Enforce TDD workflow with coverage tracking and cycle validation

## Integration

### MCP Server (Claude, Copilot, Cursor, Windsurf, VS Code, JetBrains)
```bash
cd mcp/tdd-enforcer && uv run python server.py
```

### LangChain / LangGraph
```python
from langchain.tdd_enforcer.tools import get_all_tools
tools = get_all_tools()
```

### CrewAI
```python
from crewai.tdd_enforcer.tools import *
```

### OpenAI Custom GPT
Import `openai/tdd-enforcer/openapi.json` as a GPT Action.

## License

MIT — TECHKNOWMAD LABS
