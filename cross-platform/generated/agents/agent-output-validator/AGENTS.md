# agent-output-validator

Automated validation of agent outputs against quality gates, schema compliance, and correctness criteria.

## Tools

- **validate_output**: Validate agent output against quality gates and schema

## Integration

### MCP Server (Claude, Copilot, Cursor, Windsurf, VS Code, JetBrains)
```bash
cd mcp/agent-output-validator && uv run python server.py
```

### LangChain / LangGraph
```python
from langchain.agent_output_validator.tools import get_all_tools
tools = get_all_tools()
```

### CrewAI
```python
from crewai.agent_output_validator.tools import *
```

### OpenAI Custom GPT
Import `openai/agent-output-validator/openapi.json` as a GPT Action.

## License

MIT — TECHKNOWMAD LABS
