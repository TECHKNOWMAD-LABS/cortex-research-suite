# design-system-forge

Design system generation and component library scaffolding with tokens, themes, and documentation.

## Tools

- **generate_design_system**: Generate a design system with tokens, components, and documentation

## Integration

### MCP Server (Claude, Copilot, Cursor, Windsurf, VS Code, JetBrains)
```bash
cd mcp/design-system-forge && uv run python server.py
```

### LangChain / LangGraph
```python
from langchain.design_system_forge.tools import get_all_tools
tools = get_all_tools()
```

### CrewAI
```python
from crewai.design_system_forge.tools import *
```

### OpenAI Custom GPT
Import `openai/design-system-forge/openapi.json` as a GPT Action.

## License

MIT — TECHKNOWMAD LABS
