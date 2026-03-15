# pre-package-pipeline

Skill validation and packaging pipeline for distribution-ready skill bundles.

## Tools

- **package_skill**: Validate and package a skill for distribution

## Integration

### MCP Server (Claude, Copilot, Cursor, Windsurf, VS Code, JetBrains)
```bash
cd mcp/pre-package-pipeline && uv run python server.py
```

### LangChain / LangGraph
```python
from langchain.pre_package_pipeline.tools import get_all_tools
tools = get_all_tools()
```

### CrewAI
```python
from crewai.pre_package_pipeline.tools import *
```

### OpenAI Custom GPT
Import `openai/pre-package-pipeline/openapi.json` as a GPT Action.

## License

MIT — TECHKNOWMAD LABS
