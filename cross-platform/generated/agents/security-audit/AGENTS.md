# security-audit

Automated security scanning for code repositories. Runs bandit (Python SAST), semgrep (multi-language static analysis), and secret detection to produce machine-readable reports.

## Tools

- **security_scan**: Run a full security scan on a target directory with bandit, semgrep, and secret detection

## Integration

### MCP Server (Claude, Copilot, Cursor, Windsurf, VS Code, JetBrains)
```bash
cd mcp/security-audit && uv run python server.py
```

### LangChain / LangGraph
```python
from langchain.security_audit.tools import get_all_tools
tools = get_all_tools()
```

### CrewAI
```python
from crewai.security_audit.tools import *
```

### OpenAI Custom GPT
Import `openai/security-audit/openapi.json` as a GPT Action.

## License

MIT — TECHKNOWMAD LABS