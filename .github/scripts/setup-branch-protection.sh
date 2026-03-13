#!/bin/bash
# Branch Protection Configuration Script
# This script sets up branch protection rules for the main branch
# 
# Prerequisites:
# - GitHub CLI (gh) installed and authenticated, OR
# - curl installed with a valid GitHub personal access token
# 
# Usage:
#   export GITHUB_TOKEN="your_token_here"
#   bash .github/scripts/setup-branch-protection.sh

set -e

OWNER="TECHKNOWMAD-LABS"
REPO="cortex"
BRANCH="main"
TOKEN="${GITHUB_TOKEN}"

if [ -z "$TOKEN" ]; then
  echo "Error: GITHUB_TOKEN environment variable is not set"
  echo "Please set it before running this script"
  exit 1
fi

echo "Configuring branch protection for $OWNER/$REPO (branch: $BRANCH)..."

# API endpoint for branch protection
API_URL="https://api.github.com/repos/$OWNER/$REPO/branches/$BRANCH/protection"

# Configure branch protection rules
curl -X PUT \
  -H "Authorization: token $TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  -d '{
    "required_status_checks": {
      "strict": true,
      "contexts": [
        "bandit",
        "secret-scan"
      ]
    },
    "required_pull_request_reviews": {
      "dismissal_restrictions": {},
      "require_code_owner_reviews": false,
      "required_approving_review_count": 1,
      "require_last_push_approval": false,
      "dismiss_stale_reviews": true
    },
    "enforce_admins": true,
    "required_linear_history": true,
    "allow_force_pushes": false,
    "allow_deletions": false,
    "block_creations": false,
    "required_conversation_resolution": false,
    "restrictions": null
  }' \
  "$API_URL"

echo "✓ Branch protection configured successfully"
echo ""
echo "Configuration Summary:"
echo "  - Require pull request reviews (minimum 1 reviewer)"
echo "  - Require status checks to pass (bandit, secret-scan)"
echo "  - Require branches to be up to date before merging"
echo "  - Enforce rules on administrators"
echo "  - Restrict deletions"
echo "  - Block force pushes"
echo "  - Require linear history (squash/rebase only)"
