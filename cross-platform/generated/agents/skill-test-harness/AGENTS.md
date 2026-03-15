# skill-test-harness

Automated skill testing framework with fixture management, assertion libraries, and coverage reporting.

## Tools

- **test_skill**: Run automated tests on a skill with fixtures and assertions

## Integration

### MCP Server (Claude, Copilot, Cursor, Windsurf, VS Code, JetBrains)
```bash
cd mcp/skill-test-harness && uv run python server.py
```

### LangChain / LangGraph
```python
from langchain.skill_test_harness.tools import get_all_tools
tools = get_all_tools()
```

### CrewAI
```python
from crewai.skill_test_harness.tools import *
```

### OpenAI Custom GPT
Import `openai/skill-test-harness/openapi.json` as a GPT Action.

## License

MIT — TECHKNOWMAD LABS
