# GitHub REST API v3 Patterns Reference

This document covers essential patterns for integrating with the GitHub REST API in MCP server implementations.

## Authentication Patterns

### Personal Access Token (PAT)

GitHub uses token-based authentication via the Authorization header.

```
Authorization: token YOUR_GITHUB_TOKEN
```

Token format: Typically 40 alphanumeric characters (classic) or 36+ characters (fine-grained).

**Token Scopes** (for classic PAT):
- `repo`: Full control of private/public repos
- `public_repo`: Access public repos only
- `read:repo_hook`: Read repo hooks
- `write:repo_hook`: Write repo hooks
- `gist`: Create/manage gists
- `user`: Read user profile
- `admin:repo_hook`: Admin access to repo hooks
- `delete_repo`: Delete repositories
- `workflow`: Manage GitHub Actions workflows

Fine-grained tokens have more specific permission sets (e.g., `contents:read`, `pull_requests:write`).

### Token Storage

- Store in environment variable: `GITHUB_TOKEN`
- Never commit to version control
- Use `.env` files locally, secrets management in CI/CD
- Validate token on application startup

## Common Endpoints

### Repository Operations

#### GET /repos/{owner}/{repo}
Retrieve repository metadata.

**Request:**
```
GET /repos/octocat/Hello-World
Authorization: token YOUR_GITHUB_TOKEN
```

**Response (200):**
```json
{
  "id": 1296269,
  "name": "Hello-World",
  "full_name": "octocat/Hello-World",
  "owner": {
    "login": "octocat",
    "id": 1,
    "type": "User"
  },
  "private": false,
  "description": "My first repository on GitHub!",
  "fork": false,
  "created_at": "2011-01-26T19:01:12Z",
  "updated_at": "2011-01-26T19:14:43Z",
  "pushed_at": "2011-01-26T19:06:43Z",
  "size": 180,
  "default_branch": "master",
  "language": "Python"
}
```

#### POST /user/repos
Create a new repository (requires `repo` scope).

**Request:**
```
POST /user/repos
Authorization: token YOUR_GITHUB_TOKEN
Content-Type: application/json

{
  "name": "Hello-World",
  "description": "This your first repo!",
  "private": false,
  "auto_init": true
}
```

**Response (201):**
Returns full repository object (as GET /repos/{owner}/{repo}).

**Common Parameters:**
- `name` (string, required): Repository name
- `description` (string): Repository description
- `private` (boolean): Default false
- `auto_init` (boolean): Initialize with README
- `gitignore_template` (string): e.g., "Python", "Node"
- `license_template` (string): e.g., "mit", "apache-2.0"

### File Operations

#### GET /repos/{owner}/{repo}/contents/{path}
Retrieve file or directory contents.

**Request:**
```
GET /repos/octocat/Hello-World/contents/README.md
Authorization: token YOUR_GITHUB_TOKEN
```

**Response (200) - File:**
```json
{
  "name": "README.md",
  "path": "README.md",
  "sha": "4a087b531f98c99f5d75bad70e3b9f42c95fa4b6",
  "size": 149,
  "type": "file",
  "url": "https://api.github.com/repos/octocat/Hello-World/contents/README.md",
  "html_url": "https://github.com/octocat/Hello-World/blob/master/README.md",
  "download_url": "https://raw.githubusercontent.com/octocat/Hello-World/master/README.md",
  "content": "IyBIZWxsbyBXb3JsZApUaGlzIGlzIHlvdXIgZmlyc3QgcmVwbywgY29uZ3JhdHMhCg==",
  "encoding": "base64"
}
```

**Response (200) - Directory:**
```json
[
  {
    "name": "subdir",
    "path": "subdir",
    "sha": "a1b2c3d4e5f6...",
    "size": 0,
    "type": "dir",
    "url": "https://api.github.com/repos/octocat/Hello-World/contents/subdir"
  },
  {
    "name": "file.txt",
    "path": "file.txt",
    "sha": "x7y8z9...",
    "size": 256,
    "type": "file",
    "url": "https://api.github.com/repos/octocat/Hello-World/contents/file.txt"
  }
]
```

#### PUT /repos/{owner}/{repo}/contents/{path}
Create or update a file.

**Request:**
```
PUT /repos/octocat/Hello-World/contents/README.md
Authorization: token YOUR_GITHUB_TOKEN
Content-Type: application/json

{
  "message": "Update README",
  "content": "IyBIZWxsbyBXb3JsZApUaGlzIGlzIHlvdXIgZmlyc3QgcmVwbywgY29uZ3JhdHMhCg==",
  "branch": "main",
  "sha": "4a087b531f98c99f5d75bad70e3b9f42c95fa4b6"
}
```

**Response (200/201):**
```json
{
  "content": { ... },
  "commit": {
    "sha": "7638417db6d59f3c431d3e1f261cc637155684cd",
    "url": "https://api.github.com/repos/octocat/Hello-World/git/commits/7638417...",
    "html_url": "https://github.com/octocat/Hello-World/commit/7638417...",
    "author": {
      "date": "2010-04-10T20:09:31Z",
      "name": "Scott Chacon",
      "email": "schacon@gmail.com"
    },
    "message": "Update README"
  }
}
```

**Key Points:**
- Content must be base64-encoded
- `sha` is required for updates (prevents conflicts)
- `message` is the commit message
- `branch` defaults to repository default branch

#### GET /repos/{owner}/{repo}/git/trees/{tree_sha}?recursive=1
Retrieve entire directory tree recursively.

**Request:**
```
GET /repos/octocat/Hello-World/git/trees/main?recursive=1
Authorization: token YOUR_GITHUB_TOKEN
```

**Response (200):**
```json
{
  "sha": "d123456789abcdef",
  "url": "https://api.github.com/repos/octocat/Hello-World/git/trees/d123...",
  "tree": [
    {
      "path": "README.md",
      "mode": "100644",
      "type": "blob",
      "sha": "4a087b531f98c99f5d75bad70e3b9f42c95fa4b6",
      "size": 149,
      "url": "https://api.github.com/repos/octocat/Hello-World/git/blobs/4a08..."
    },
    {
      "path": "src/main.py",
      "mode": "100644",
      "type": "blob",
      "sha": "a1b2c3d4e5f6...",
      "size": 512,
      "url": "https://api.github.com/repos/octocat/Hello-World/git/blobs/a1b2..."
    },
    {
      "path": "src",
      "mode": "040000",
      "type": "tree",
      "sha": "x7y8z9...",
      "url": "https://api.github.com/repos/octocat/Hello-World/git/trees/x7y8..."
    }
  ],
  "truncated": false
}
```

### Pull Request Operations

#### POST /repos/{owner}/{repo}/pulls
Create a pull request.

**Request:**
```
POST /repos/octocat/Hello-World/pulls
Authorization: token YOUR_GITHUB_TOKEN
Content-Type: application/json

{
  "title": "Add feature X",
  "body": "This PR adds feature X.\n\nCloses #123",
  "head": "feature-branch",
  "base": "main"
}
```

**Response (201):**
```json
{
  "id": 1,
  "number": 1347,
  "state": "open",
  "title": "Add feature X",
  "body": "This PR adds feature X.",
  "created_at": "2011-01-26T19:01:12Z",
  "updated_at": "2011-01-26T19:01:12Z",
  "closed_at": null,
  "merged_at": null,
  "head": {
    "label": "octocat:feature-branch",
    "ref": "feature-branch",
    "sha": "6dcb09b5b57875f334f61aebed695e2e4193db5e"
  },
  "base": {
    "label": "octocat:main",
    "ref": "main",
    "sha": "6dcb09b5b57875f334f61aebed695e2e4193db5e"
  },
  "user": {
    "login": "octocat",
    "id": 1
  },
  "html_url": "https://github.com/octocat/Hello-World/pull/1347"
}
```

#### GET /repos/{owner}/{repo}/pulls/{pull_number}
Retrieve pull request details.

**Request:**
```
GET /repos/octocat/Hello-World/pulls/1347
Authorization: token YOUR_GITHUB_TOKEN
```

**Response (200):**
Returns pull request object (as POST response above).

### Issue Operations

#### POST /repos/{owner}/{repo}/issues
Create an issue.

**Request:**
```
POST /repos/octocat/Hello-World/issues
Authorization: token YOUR_GITHUB_TOKEN
Content-Type: application/json

{
  "title": "Found a bug",
  "body": "I'm having a problem with this.",
  "labels": ["bug", "help wanted"],
  "assignees": ["octocat"]
}
```

**Response (201):**
```json
{
  "id": 1,
  "number": 1347,
  "title": "Found a bug",
  "body": "I'm having a problem with this.",
  "state": "open",
  "created_at": "2011-04-22T13:33:48Z",
  "updated_at": "2011-04-22T13:33:48Z",
  "closed_at": null,
  "labels": [
    {
      "id": 208045946,
      "name": "bug",
      "color": "f29513"
    },
    {
      "id": 208045947,
      "name": "help wanted",
      "color": "cccccc"
    }
  ],
  "assignees": [
    {
      "login": "octocat",
      "id": 1
    }
  ],
  "html_url": "https://github.com/octocat/Hello-World/issues/1347"
}
```

### Release Operations

#### POST /repos/{owner}/{repo}/releases
Create a release.

**Request:**
```
POST /repos/octocat/Hello-World/releases
Authorization: token YOUR_GITHUB_TOKEN
Content-Type: application/json

{
  "tag_name": "v1.0.0",
  "target_commitish": "main",
  "name": "Release 1.0.0",
  "body": "Initial release",
  "draft": false,
  "prerelease": false
}
```

**Response (201):**
```json
{
  "id": 1,
  "tag_name": "v1.0.0",
  "target_commitish": "main",
  "name": "Release 1.0.0",
  "body": "Initial release",
  "draft": false,
  "prerelease": false,
  "created_at": "2013-02-27T19:35:32Z",
  "published_at": "2013-02-27T19:35:32Z",
  "author": {
    "login": "octocat",
    "id": 1
  },
  "html_url": "https://github.com/octocat/Hello-World/releases/tag/v1.0.0",
  "assets": []
}
```

## Pagination

GitHub uses cursor-based pagination via the `Link` header for large result sets.

**Request:**
```
GET /repos/octocat/Hello-World/issues?per_page=30&page=2
Authorization: token YOUR_GITHUB_TOKEN
```

**Response Header:**
```
Link: <https://api.github.com/repos/octocat/Hello-World/issues?page=3>; rel="next", <https://api.github.com/repos/octocat/Hello-World/issues?page=50>; rel="last"
```

**Key Points:**
- `per_page`: Results per page (default 30, max 100)
- `page`: Page number (default 1)
- Parse `Link` header for navigation
- Recommended: Follow `rel="next"` for iterating results

## Rate Limiting

GitHub enforces rate limits on API requests.

**Authenticated Requests:** 5000 requests per hour
**Unauthenticated Requests:** 60 requests per hour

### Rate Limit Headers

All responses include rate limit information:

```
X-RateLimit-Limit: 5000
X-RateLimit-Remaining: 4999
X-RateLimit-Reset: 1372700873
```

The `X-RateLimit-Reset` value is a Unix timestamp (seconds since epoch).

**Checking Rate Limit:**
```
GET /rate_limit
Authorization: token YOUR_GITHUB_TOKEN
```

**Response:**
```json
{
  "resources": {
    "core": {
      "limit": 5000,
      "remaining": 4999,
      "reset": 1372700873
    },
    "search": {
      "limit": 30,
      "remaining": 28,
      "reset": 1372697452
    }
  },
  "rate": {
    "limit": 5000,
    "remaining": 4999,
    "reset": 1372700873
  }
}
```

## Error Handling

GitHub returns structured error responses with descriptive messages.

### 401 Unauthorized

Missing or invalid authentication.

**Response:**
```json
{
  "message": "Bad credentials",
  "documentation_url": "https://docs.github.com/rest/overview/resources-in-the-rest-api#authentication"
}
```

**Causes:** Expired token, invalid token, missing header

### 403 Forbidden

Authenticated but lacks required permissions.

**Response:**
```json
{
  "message": "API rate limit exceeded for user ID 1234.",
  "documentation_url": "https://docs.github.com/rest/overview/resources-in-the-rest-api#rate-limiting"
}
```

**Causes:** Rate limit exceeded, insufficient token scopes, branch protection

### 404 Not Found

Resource does not exist.

**Response:**
```json
{
  "message": "Not Found",
  "documentation_url": "https://docs.github.com/rest/reference/repos#get-a-repository"
}
```

### 422 Unprocessable Entity

Validation error in request body.

**Response:**
```json
{
  "message": "Validation Failed",
  "errors": [
    {
      "resource": "PullRequest",
      "field": "base",
      "code": "invalid"
    }
  ],
  "documentation_url": "https://docs.github.com/rest/reference/pulls#create-a-pull-request"
}
```

**Common Causes:**
- Branch does not exist
- SHA mismatch (for file updates)
- Invalid field values

## Content Encoding

File contents in GitHub API are base64-encoded.

**Encoding to base64 (Python):**
```python
import base64
content = "Hello, World!"
encoded = base64.b64encode(content.encode()).decode()
# Result: "SGVsbG8sIFdvcmxkIQ=="
```

**Decoding from base64 (Python):**
```python
import base64
encoded = "SGVsbG8sIFdvcmxkIQ=="
decoded = base64.b64decode(encoded).decode()
# Result: "Hello, World!"
```

This applies to:
- File contents in GET/PUT `/repos/{owner}/{repo}/contents/{path}`
- Creating/updating files via tree operations

## Common Pitfalls

### 1. SHA Required for File Updates

When updating a file via PUT `/repos/{owner}/{repo}/contents/{path}`, always include the current file SHA. Omitting it causes a 422 error.

```
PUT /repos/octocat/Hello-World/contents/README.md

{
  "message": "Update README",
  "content": "...",
  "sha": "4a087b531f98c99f5d75bad70e3b9f42c95fa4b6"
}
```

**Workflow:**
1. GET file to retrieve current SHA
2. Modify content and base64-encode
3. PUT with new content and original SHA

### 2. Branch Protection

Repositories with branch protection may reject direct pushes or PR merges.

**Error:**
```json
{
  "message": "Blocked by branch protection",
  "code": "branch_protection"
}
```

**Solution:** Use workflow via pull requests; ensure branch protection rules allow your token/user.

### 3. Token Scope Mismatch

Attempting actions without required scopes returns 403.

**Example:** Trying to create a repo with `public_repo` scope (insufficient).

**Solution:** Verify token scopes match intended operations. Use fine-grained tokens for minimal privilege.

### 4. Content Encoding Errors

Forgetting to base64-encode file content causes validation errors.

**Bad:**
```json
{
  "message": "Validation Failed",
  "errors": [
    {
      "resource": "Content",
      "field": "content",
      "code": "invalid"
    }
  ]
}
```

**Good:** Always base64-encode before sending.

### 5. Pagination Limits

Requesting page numbers beyond available results returns empty array.

**Recommendation:** Parse `Link` header instead of guessing page count.

### 6. Concurrent Edits

Multiple concurrent edits to the same file can cause SHA conflicts.

**Error:**
```json
{
  "message": "SHA does not match",
  "code": "sha_mismatch"
}
```

**Solution:** Implement retry logic with fresh SHA retrieval on conflict.
