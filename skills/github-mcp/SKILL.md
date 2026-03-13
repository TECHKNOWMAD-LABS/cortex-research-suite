---
name: github-mcp
description: >
  Build and deploy a GitHub MCP server for repository management. Use when the
  user needs GitHub API integration, wants to push files without browser
  automation, manage repos/PRs/issues via API, or mentions "GitHub MCP",
  "GitHub connector", "push to GitHub via API", or "GitHub integration".
---

# GitHub MCP Server Builder

Build a complete Model Context Protocol (MCP) server that integrates with GitHub's REST API for programmatic repository, pull request, issue, and release management. This skill instantiates the mcp-builder pattern specifically for GitHub workflows.

## Quick Start

```bash
python3 scripts/bootstrap.py
export GITHUB_PAT="your_personal_access_token_here"
python3 src/server.py
```

Then connect to the server from Claude Code or other MCP clients via stdio transport.

## Tool Inventory

The GitHub MCP server implements these tools for Claude to call:

### Repository Management
- **github_get_repo** — Get repository metadata (name, description, stars, forks, visibility)
- **github_list_repos** — List user's repositories with filtering and sorting
- **github_update_repo_settings** — Update description, topics, website, visibility

### File Operations
- **github_create_or_update_file** — Create or update a single file (commits via API)
- **github_get_file_contents** — Retrieve file content from any branch
- **github_delete_file** — Delete a file and commit the deletion

### Branching & Commits
- **github_list_commits** — List commits on a branch with author/message filtering
- **github_create_branch** — Create a new branch from a specific commit/ref
- **github_list_branches** — List all branches with protection status

### Pull Requests
- **github_create_pull_request** — Create a PR with title, body, base/head branches
- **github_list_pull_requests** — List PRs with filtering by state (open/closed/all)
- **github_merge_pull_request** — Merge a PR with configurable merge strategy

### Issues
- **github_create_issue** — Create an issue with title, body, labels, assignees
- **github_list_issues** — List issues with filtering by state, labels, assignee

### Releases
- **github_create_release** — Create a release with tag, name, body, assets

## Architecture

### Project Structure
```
github-mcp/
├── src/
│   ├── server.py              # FastMCP server entry point
│   ├── github_client.py        # GitHub API wrapper (requests library)
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── repos.py           # Repository tools
│   │   ├── files.py           # File operation tools
│   │   ├── branches.py        # Branch and commit tools
│   │   ├── pull_requests.py   # PR tools
│   │   ├── issues.py          # Issue tools
│   │   └── releases.py        # Release tools
│   └── exceptions.py          # Custom exception classes
├── scripts/
│   ├── bootstrap.py           # Scaffolds the full project
│   └── test_connection.py     # Validates GitHub PAT and API access
├── requirements.txt
└── README.md
```

### Authentication

Use GitHub Personal Access Token (PAT) for authentication. The server reads the token from the `GITHUB_PAT` environment variable at startup.

```bash
export GITHUB_PAT="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

**Required Scopes:**
- `repo` — Full control of repositories (read/write)
- `workflow` — Access to workflows (if managing GitHub Actions)
- `public_repo` — Access to public repositories only (minimal scope)

Generate a PAT at: https://github.com/settings/tokens

### FastMCP Server Pattern

```python
from fastmcp import FastMCP
import os

app = FastMCP("github-mcp")
GITHUB_PAT = os.getenv("GITHUB_PAT")
GITHUB_API = "https://api.github.com"

if not GITHUB_PAT:
    raise ValueError("GITHUB_PAT environment variable not set")

# Initialize GitHub client
client = GitHubClient(GITHUB_PAT)

# Register tools
@app.tool()
def github_get_repo(owner: str, repo: str) -> dict:
    """Fetch repository metadata"""
    return client.get_repo(owner, repo)

@app.tool()
def github_list_repos(owner: str, per_page: int = 30) -> list:
    """List repositories with pagination"""
    return client.list_repos(owner, per_page=per_page)

# ... more tools ...

if __name__ == "__main__":
    app.run()
```

### GitHub Client Implementation Pattern

```python
import requests
from typing import Optional, Dict, List, Any

class GitHubClient:
    def __init__(self, pat: str):
        self.token = pat
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {pat}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make authenticated API request with error handling"""
        url = f"{self.base_url}{endpoint}"
        response = requests.request(method, url, headers=self.headers, **kwargs)
        
        # Handle rate limiting
        if response.status_code == 403 and "API rate limit exceeded" in response.text:
            raise RateLimitError(f"GitHub API rate limit exceeded. Reset at {response.headers.get('X-RateLimit-Reset')}")
        
        # Handle not found
        if response.status_code == 404:
            raise NotFoundError(f"Resource not found: {endpoint}")
        
        # Handle validation errors
        if response.status_code == 422:
            errors = response.json().get("errors", [])
            raise ValidationError(f"GitHub validation error: {errors}")
        
        response.raise_for_status()
        return response.json() if response.text else {}
    
    def get_repo(self, owner: str, repo: str) -> Dict[str, Any]:
        """GET /repos/{owner}/{repo}"""
        return self._request("GET", f"/repos/{owner}/{repo}")
    
    def list_repos(self, owner: str, per_page: int = 30, page: int = 1) -> List[Dict]:
        """GET /users/{owner}/repos with pagination"""
        params = {"per_page": min(per_page, 100), "page": page, "type": "all"}
        return self._request("GET", f"/users/{owner}/repos", params=params)
```

### Tool Implementation Patterns

#### File Operations Pattern
```python
def github_create_or_update_file(owner: str, repo: str, path: str, 
                                  content: str, message: str, 
                                  branch: str = "main", sha: Optional[str] = None) -> Dict:
    """Create or update a file in the repository"""
    endpoint = f"/repos/{owner}/{repo}/contents/{path}"
    
    # Encode content to base64
    import base64
    encoded_content = base64.b64encode(content.encode()).decode()
    
    payload = {
        "message": message,
        "content": encoded_content,
        "branch": branch
    }
    
    # If updating, include the current file's SHA
    if sha:
        payload["sha"] = sha
    
    return client._request("PUT", endpoint, json=payload)
```

#### Pull Request Pattern
```python
def github_create_pull_request(owner: str, repo: str, title: str, 
                               head: str, base: str = "main", 
                               body: str = "") -> Dict:
    """Create a new pull request"""
    endpoint = f"/repos/{owner}/{repo}/pulls"
    
    payload = {
        "title": title,
        "head": head,
        "base": base,
        "body": body
    }
    
    return client._request("POST", endpoint, json=payload)
```

#### Pagination Pattern
```python
def github_list_commits(owner: str, repo: str, branch: str = "main", 
                        per_page: int = 30) -> List[Dict]:
    """List commits with pagination support"""
    endpoint = f"/repos/{owner}/{repo}/commits"
    params = {
        "sha": branch,
        "per_page": min(per_page, 100),
        "page": 1
    }
    
    commits = []
    while True:
        response = client._request("GET", endpoint, params=params)
        commits.extend(response)
        
        # Check for next page via Link header
        if "Link" not in client.headers or 'rel="next"' not in client.headers.get("Link", ""):
            break
        
        params["page"] += 1
    
    return commits
```

### Error Handling

Implement custom exception classes for GitHub API errors:

```python
class GitHubError(Exception):
    """Base exception for GitHub API errors"""
    pass

class RateLimitError(GitHubError):
    """Raised when GitHub API rate limit is exceeded"""
    pass

class NotFoundError(GitHubError):
    """Raised when a resource is not found (404)"""
    pass

class ValidationError(GitHubError):
    """Raised when GitHub rejects the request due to validation (422)"""
    pass

class AuthenticationError(GitHubError):
    """Raised when authentication fails (401)"""
    pass
```

## Implementation Checklist

- [ ] Create project structure with `scripts/bootstrap.py`
- [ ] Implement `GitHubClient` class with authentication and request handling
- [ ] Implement repository management tools (get_repo, list_repos, update_settings)
- [ ] Implement file operation tools (create_or_update, get_contents, delete)
- [ ] Implement branching tools (create_branch, list_branches, list_commits)
- [ ] Implement PR tools (create, list, merge)
- [ ] Implement issue tools (create, list)
- [ ] Implement release tools (create_release)
- [ ] Add comprehensive error handling for rate limits, 404s, 422s
- [ ] Add pagination support for list endpoints (default 30 items per page)
- [ ] Test with `scripts/test_connection.py` before deployment
- [ ] Document each tool with input/output schemas
- [ ] Add rate limit awareness and retry logic

## Scripts

### scripts/bootstrap.py
Scaffolds the complete MCP project structure from this skill template. Creates all directories, installs dependencies, and generates tool boilerplate.

Usage:
```bash
python3 scripts/bootstrap.py --output ./my-github-mcp
```

### scripts/test_connection.py
Validates GitHub PAT and verifies API access by making a test API call (e.g., fetching the authenticated user).

Usage:
```bash
export GITHUB_PAT="your_token_here"
python3 scripts/test_connection.py
```

Output: Connection status, rate limit info, authenticated user info.

## Configuration

### requirements.txt
```
fastmcp>=0.1.0
requests>=2.31.0
python-dotenv>=1.0.0
```

### Environment Variables
- `GITHUB_PAT` — GitHub Personal Access Token (required)
- `GITHUB_API_BASE` — API base URL (default: https://api.github.com)
- `LOG_LEVEL` — Logging level (default: INFO)

## API Reference

See `references/github-api-patterns.md` for:
- Complete endpoint documentation
- Request/response examples for each tool
- Rate limiting details and best practices
- Pagination cursor patterns
- Branch protection rule endpoints
- Workflow and Actions API patterns

## Key Features

1. **Atomic File Operations** — Push changes without browser automation
2. **PR Workflow Automation** — Create, list, and merge PRs programmatically
3. **Issue Management** — Create and filter issues via API
4. **Branch Safety** — Create branches, list protection rules
5. **Rate Limit Awareness** — Handle GitHub's 60 req/hr (unauthenticated) or 5000 req/hr (authenticated)
6. **Error Recovery** — Graceful handling of 404s, 422s, and rate limits
7. **Pagination** — Automatic handling of large result sets

## Integration with Claude Code

Once deployed, use the GitHub MCP server in Claude Code workflows:

```python
# Push changes directly to GitHub
result = mcp.tools.github_create_or_update_file(
    owner="myorg",
    repo="myrepo",
    path="src/feature.py",
    content="new code here",
    message="feat: add new feature",
    branch="feature-branch"
)

# Create a PR from the feature branch
pr = mcp.tools.github_create_pull_request(
    owner="myorg",
    repo="myrepo",
    title="Add new feature",
    head="feature-branch",
    base="main",
    body="This PR adds..."
)
```

## Troubleshooting

**"GITHUB_PAT not set"** — Set the environment variable before running the server.

**"401 Unauthorized"** — PAT may be expired or revoked. Generate a new one at github.com/settings/tokens.

**"403 API rate limit exceeded"** — Wait until the reset time shown in the error, or use a PAT with higher limits.

**"422 Validation failed"** — Check the error details returned. Common causes: invalid branch name, file already exists, invalid commit message.

**"404 Not Found"** — Repository or resource doesn't exist, or PAT lacks permission to access it.

## References

- GitHub REST API Docs: https://docs.github.com/en/rest
- MCP Specification: https://modelcontextprotocol.io
- FastMCP: https://github.com/jlotz/FastMCP
- Personal Access Tokens: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens
