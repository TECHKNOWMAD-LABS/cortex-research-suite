# prompt-architect

Prompt engineering and optimization. Analyzes, improves, and tests prompts for AI/ML tasks and agent systems.

## Tools

- **optimize_prompt**: Analyze and optimize a prompt for improved performance

## Integration

### MCP Server (Claude, Copilot, Cursor, Windsurf, VS Code, JetBrains)
```bash
cd mcp/prompt-architect && uv run python server.py
```

### LangChain / LangGraph
```python
from langchain.prompt_architect.tools import get_all_tools
tools = get_all_tools()
```

### CrewAI
```python
from crewai.prompt_architect.tools import *
```

### OpenAI Custom GPT
Import `openai/prompt-architect/openapi.json` as a GPT Action.

## License

MIT — TECHKNOWMAD LABS
