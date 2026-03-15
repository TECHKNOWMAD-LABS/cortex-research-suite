# github-mcp

GitHub API integration via Model Context Protocol for repository management, PRs, issues, and releases.

## Tools

- **github_operation**: Execute GitHub API operations via MCP

## Integration

### MCP Server (Claude, Copilot, Cursor, Windsurf, VS Code, JetBrains)
```bash
cd mcp/github-mcp && uv run python server.py
```

### LangChain / LangGraph
```python
from langchain.github_mcp.tools import get_all_tools
tools = get_all_tools()
```

### CrewAI
```python
from crewai.github_mcp.tools import *
```

### OpenAI Custom GPT
Import `openai/github-mcp/openapi.json` as a GPT Action.

## License

MIT — TECHKNOWMAD LABS
