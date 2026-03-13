#!/usr/bin/env python3
"""
GitHub Personal Access Token (PAT) Verification

Validates that a GitHub token is valid and displays token metadata.
Uses only Python standard library (urllib).

Exit codes:
    0 - Token is valid
    1 - Token is invalid or missing
    2 - Error reading environment/config
"""

import urllib.request
import urllib.error
import json
import os
import sys
from pathlib import Path
from datetime import datetime


def load_env_file(env_path=".env"):
    """Load environment variables from .env file."""
    env_vars = {}
    if os.path.exists(env_path):
        try:
            with open(env_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        key, value = line.split("=", 1)
                        env_vars[key.strip()] = value.strip()
        except Exception as e:
            print(f"Warning: Could not read {env_path}: {e}")
    return env_vars


def get_github_token():
    """Get GitHub token from environment or .env file."""
    # First check environment variable
    token = os.getenv("GITHUB_TOKEN")
    if token:
        return token

    # Then check .env file in current directory
    env_vars = load_env_file(".env")
    if "GITHUB_TOKEN" in env_vars:
        return env_vars["GITHUB_TOKEN"]

    return None


def verify_token(token):
    """
    Verify GitHub token by calling the API.

    Args:
        token: GitHub personal access token

    Returns:
        Tuple of (success: bool, user_data: dict or error_message: str)
    """
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "github-mcp-verify/0.1.0",
    }

    # SECURITY: URL validated to api.github.com only
    # Request user info
    req = urllib.request.Request(
        "https://api.github.com/user",
        headers=headers,
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            return True, data
    except urllib.error.HTTPError as e:
        if e.code == 401:
            return False, "Invalid token (401 Unauthorized)"
        elif e.code == 403:
            return False, "Token forbidden (403 Forbidden)"
        else:
            error_body = e.read().decode()
            try:
                error_data = json.loads(error_body)
                return False, f"HTTP {e.code}: {error_data.get('message', str(e))}"
            except:
                return False, f"HTTP {e.code}: {str(e)}"
    except urllib.error.URLError as e:
        return False, f"Network error: {str(e)}"
    except Exception as e:
        return False, f"Error: {type(e).__name__}: {str(e)}"


def get_rate_limit(token):
    """
    Get GitHub API rate limit information.

    Args:
        token: GitHub personal access token

    Returns:
        Tuple of (success: bool, rate_limit_data: dict or error_message: str)
    """
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "github-mcp-verify/0.1.0",
    }

    # SECURITY: URL validated to api.github.com only
    req = urllib.request.Request(
        "https://api.github.com/rate_limit",
        headers=headers,
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            core = data.get("resources", {}).get("core", {})
            return True, {
                "remaining": core.get("remaining"),
                "limit": core.get("limit"),
                "reset": core.get("reset"),
            }
    except Exception as e:
        return False, str(e)


def format_timestamp(unix_timestamp):
    """Convert Unix timestamp to human-readable format."""
    try:
        return datetime.fromtimestamp(unix_timestamp).strftime("%Y-%m-%d %H:%M:%S UTC")
    except:
        return "Unknown"


def main():
    """Main entry point."""
    print("GitHub Token Verification\n" + "=" * 50)

    # Get token
    token = get_github_token()
    if not token:
        print("Error: GITHUB_TOKEN not found in environment or .env file")
        print("\nTo fix this:")
        print("  1. Create a .env file in the current directory")
        print("  2. Add: GITHUB_TOKEN=ghp_your_token_here")
        print("  3. Or set environment variable: export GITHUB_TOKEN=ghp_...")
        return 1

    print(f"Token found (length: {len(token)} characters)\n")

    # Verify token
    print("Verifying token...")
    success, result = verify_token(token)

    if not success:
        print(f"Status: INVALID")
        print(f"Error: {result}\n")
        return 1

    # Token is valid
    print(f"Status: VALID\n")

    user_data = result
    print("User Information:")
    print(f"  Login: {user_data.get('login')}")
    print(f"  Name: {user_data.get('name')}")
    print(f"  Company: {user_data.get('company')}")
    print(f"  Location: {user_data.get('location')}")
    print(f"  Bio: {user_data.get('bio')}")
    print(f"  Public repos: {user_data.get('public_repos')}")
    print(f"  Followers: {user_data.get('followers')}")

    # Get rate limit
    print("\nChecking rate limits...")
    success, rate_data = get_rate_limit(token)

    if success:
        print(f"Rate Limit Status:")
        print(f"  Remaining: {rate_data['remaining']}/{rate_data['limit']}")
        reset_time = format_timestamp(rate_data['reset'])
        print(f"  Resets at: {reset_time}")
    else:
        print(f"Could not retrieve rate limit information: {rate_data}")

    print("\n" + "=" * 50)
    print("Token verification successful!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
