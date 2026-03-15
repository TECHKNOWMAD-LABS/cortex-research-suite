# agent-orchestrator

Multi-agent coordination and task dispatch with dynamic routing and load balancing.

## Tools

- **orchestrate_agents**: Coordinate multiple agents to execute tasks with dynamic routing

## Integration

### MCP Server (Claude, Copilot, Cursor, Windsurf, VS Code, JetBrains)
```bash
cd mcp/agent-orchestrator && uv run python server.py
```

### LangChain / LangGraph
```python
from langchain.agent_orchestrator.tools import get_all_tools
tools = get_all_tools()
```

### CrewAI
```python
from crewai.agent_orchestrator.tools import *
```

### OpenAI Custom GPT
Import `openai/agent-orchestrator/openapi.json` as a GPT Action.

## License

MIT — TECHKNOWMAD LABS
