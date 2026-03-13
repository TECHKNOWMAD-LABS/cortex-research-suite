#!/usr/bin/env python3
"""
Bootstrap a new GitHub MCP server project.

Creates a complete project structure with dependencies, configuration,
and example tools to get started quickly.

Usage:
    python bootstrap.py --name my-github-mcp --output ./
    python bootstrap.py --name my-github-mcp  # Defaults to current directory
"""

import argparse
import os
import sys
from pathlib import Path


def create_directory_structure(project_dir):
    """Create the base directory structure."""
    directories = [
        project_dir,
        project_dir / "src",
        project_dir / "tests",
        project_dir / ".github",
        project_dir / ".github" / "workflows",
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    print(f"Created directory structure in {project_dir}")


def create_requirements_txt(project_dir):
    """Create requirements.txt with dependencies."""
    content = """fastmcp>=0.1.0
httpx>=0.24.0
python-dotenv>=1.0.0
"""
    file_path = project_dir / "requirements.txt"
    file_path.write_text(content)
    print(f"Created {file_path}")


def create_env_example(project_dir):
    """Create .env.example with template variables."""
    content = """# GitHub API Configuration
GITHUB_TOKEN=ghp_your_personal_access_token_here

# MCP Server Configuration (optional)
DEBUG=false
LOG_LEVEL=info
"""
    file_path = project_dir / ".env.example"
    file_path.write_text(content)
    print(f"Created {file_path}")


def create_pyproject_toml(project_dir, project_name):
    """Create pyproject.toml with project metadata."""
    content = f"""[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "{project_name}"
version = "0.1.0"
description = "GitHub MCP server for model context protocol integration"
readme = "README.md"
requires-python = ">=3.8"
license = {{text = "MIT"}}
authors = [
    {{name = "Your Name", email = "you@example.com"}},
]
dependencies = [
    "fastmcp>=0.1.0",
    "httpx>=0.24.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.0",
    "ruff>=0.1.0",
]

[tool.setuptools]
packages = ["src"]

[tool.black]
line-length = 88
target-version = ["py38", "py39", "py310", "py311"]

[tool.ruff]
line-length = 88
target-version = "py38"
select = ["E", "F", "W", "I"]
"""
    file_path = project_dir / "pyproject.toml"
    file_path.write_text(content)
    print(f"Created {file_path}")


def create_server_py(project_dir):
    """Create src/server.py with FastMCP setup and example tool."""
    content = '''"""
GitHub MCP Server

A Model Context Protocol server providing GitHub API integration for AI models.
"""

import os
import json
import httpx
from typing import Any
from fastmcp import FastMCP
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP(name="github-mcp", version="0.1.0")

# GitHub API configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_API_BASE = "https://api.github.com"
DEFAULT_TIMEOUT = 30.0


def get_auth_headers() -> dict[str, str]:
    """Get authenticated headers for GitHub API requests."""
    if not GITHUB_TOKEN:
        raise ValueError("GITHUB_TOKEN environment variable not set")
    return {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "github-mcp/0.1.0",
    }


@mcp.tool()
async def get_user_info() -> dict[str, Any]:
    """
    Retrieve authenticated user information.

    Returns:
        Dictionary containing user profile data (login, name, bio, location, etc.)
    """
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        response = await client.get(
            f"{GITHUB_API_BASE}/user",
            headers=get_auth_headers(),
        )
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_repo_info(owner: str, repo: str) -> dict[str, Any]:
    """
    Retrieve repository metadata.

    Args:
        owner: Repository owner login
        repo: Repository name

    Returns:
        Dictionary containing repository information (name, description, stars, etc.)
    """
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        response = await client.get(
            f"{GITHUB_API_BASE}/repos/{owner}/{repo}",
            headers=get_auth_headers(),
        )
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def check_rate_limit() -> dict[str, Any]:
    """
    Check GitHub API rate limit status.

    Returns:
        Dictionary with remaining requests and reset time
    """
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        response = await client.get(
            f"{GITHUB_API_BASE}/rate_limit",
            headers=get_auth_headers(),
        )
        response.raise_for_status()
        data = response.json()
        return {
            "remaining": data["resources"]["core"]["remaining"],
            "limit": data["resources"]["core"]["limit"],
            "reset": data["resources"]["core"]["reset"],
        }


if __name__ == "__main__":
    # Run the server
    mcp.run()
'''
    file_path = project_dir / "src" / "server.py"
    file_path.write_text(content)
    print(f"Created {file_path}")


def create_test_connection(project_dir):
    """Create tests/test_connection.py that validates the token works."""
    content = '''"""
Test GitHub API connection.

Validates that the GITHUB_TOKEN is valid and has appropriate scopes.
"""

import asyncio
import httpx
import os
from pathlib import Path


async def test_github_connection():
    """Test GitHub API connection and authentication."""
    token = os.getenv("GITHUB_TOKEN")

    if not token:
        print("ERROR: GITHUB_TOKEN not set")
        return False

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "github-mcp-test/0.1.0",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            # Test user endpoint
            print("Testing GitHub authentication...")
            response = await client.get(
                "https://api.github.com/user",
                headers=headers,
            )

            if response.status_code == 401:
                print("ERROR: Invalid token (401 Unauthorized)")
                return False
            elif response.status_code == 403:
                print("ERROR: Token forbidden (403 Forbidden)")
                return False
            elif response.status_code != 200:
                print(f"ERROR: Unexpected status {response.status_code}")
                return False

            user_data = response.json()
            print(f"Authenticated as: {user_data.get('login')}")
            print(f"Name: {user_data.get('name')}")
            print(f"Company: {user_data.get('company')}")
            print(f"Location: {user_data.get('location')}")

            # Get rate limit information
            print("\\nChecking rate limits...")
            rate_response = await client.get(
                "https://api.github.com/rate_limit",
                headers=headers,
            )

            if rate_response.status_code == 200:
                rate_data = rate_response.json()
                core = rate_data["resources"]["core"]
                print(f"Remaining requests: {core['remaining']}/{core['limit']}")

                import time
                reset_time = time.strftime(
                    "%Y-%m-%d %H:%M:%S",
                    time.localtime(core["reset"])
                )
                print(f"Rate limit reset: {reset_time}")
            else:
                print("Could not retrieve rate limit information")

            print("\\nGitHub API connection successful!")
            return True

        except Exception as e:
            print(f"ERROR: {type(e).__name__}: {e}")
            return False


if __name__ == "__main__":
    # Load .env if it exists
    env_path = Path(".env")
    if env_path.exists():
        from dotenv import load_dotenv
        load_dotenv(env_path)

    success = asyncio.run(test_github_connection())
    exit(0 if success else 1)
'''
    file_path = project_dir / "tests" / "test_connection.py"
    file_path.write_text(content)
    print(f"Created {file_path}")


def create_readme(project_dir, project_name):
    """Create README.md with setup instructions."""
    content = f"""# {project_name}

A GitHub MCP server for model context protocol integration.

## Installation

### Prerequisites

- Python 3.8 or higher
- pip or uv package manager
- GitHub personal access token

### Setup

1. Clone or download this project:
   ```bash
   cd {project_name}
   ```

2. Create a Python virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create `.env` file with your GitHub token:
   ```bash
   cp .env.example .env
   # Edit .env and add your GITHUB_TOKEN
   ```

   Generate a personal access token:
   - Go to https://github.com/settings/tokens
   - Click "Generate new token" > "Generate new token (classic)"
   - Select scopes: `repo`, `read:user`, `user:email`
   - Copy the token to `.env`

5. Test the connection:
   ```bash
   python tests/test_connection.py
   ```

## Usage

Start the MCP server:
```bash
python src/server.py
```

The server will start and expose tools for GitHub API interaction.

## Available Tools

The server provides the following tools:

- **get_user_info**: Retrieve authenticated user profile information
- **get_repo_info**: Get repository metadata (owner, repo name)
- **check_rate_limit**: Check GitHub API rate limit status

## Development

### Code Style

Format code with Black:
```bash
black src/ tests/
```

### Running Tests

```bash
pytest tests/
```

### Adding New Tools

Edit `src/server.py` and add new tools:

```python
@mcp.tool()
async def my_tool(param: str) -> dict:
    \"\"\"Tool description.\"\"\"
    # Implementation
    pass
```

## API Documentation

See `references/github-api-patterns.md` for GitHub REST API patterns and examples.

## Troubleshooting

### "GITHUB_TOKEN environment variable not set"

Ensure `.env` file exists and contains `GITHUB_TOKEN=...`

### "Bad credentials" or 401 error

Token is invalid or expired. Generate a new one from https://github.com/settings/tokens

### Rate limit exceeded

Wait for rate limit reset (shown in `check_rate_limit` output) or use a token with higher limits.

## License

MIT
"""
    file_path = project_dir / "README.md"
    file_path.write_text(content)
    print(f"Created {file_path}")


def create_gitignore(project_dir):
    """Create .gitignore file."""
    content = """# Virtual environments
venv/
env/
ENV/
.venv

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Environment
.env
.env.local
.env.*.local

# Pytest
.pytest_cache/
.coverage
htmlcov/

# Project specific
*.log
"""
    file_path = project_dir / ".gitignore"
    file_path.write_text(content)
    print(f"Created {file_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Bootstrap a new GitHub MCP server project"
    )
    parser.add_argument(
        "--name",
        required=True,
        help="Project name (e.g., my-github-mcp)",
    )
    parser.add_argument(
        "--output",
        default=".",
        help="Output directory (default: current directory)",
    )

    args = parser.parse_args()

    # Create output directory
    output_path = Path(args.output)
    project_dir = output_path / args.name

    # Check if project already exists
    if project_dir.exists():
        print(f"ERROR: Directory {project_dir} already exists")
        sys.exit(1)

    print(f"Creating new GitHub MCP project: {args.name}")
    print(f"Output directory: {project_dir}\n")

    # Create project structure
    create_directory_structure(project_dir)
    create_requirements_txt(project_dir)
    create_env_example(project_dir)
    create_pyproject_toml(project_dir, args.name)
    create_server_py(project_dir)
    create_test_connection(project_dir)
    create_readme(project_dir, args.name)
    create_gitignore(project_dir)

    print("\n" + "=" * 60)
    print(f"Project created successfully!")
    print(f"\nNext steps:")
    print(f"  cd {project_dir}")
    print(f"  python3 -m venv venv")
    print(f"  source venv/bin/activate")
    print(f"  pip install -r requirements.txt")
    print(f"  cp .env.example .env")
    print(f"  # Edit .env with your GITHUB_TOKEN")
    print(f"  python tests/test_connection.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
