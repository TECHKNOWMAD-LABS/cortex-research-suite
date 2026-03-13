# Enterprise Setup Runbook

Manual configuration steps for TECHKNOWMAD-LABS GitHub organization.
These require UI access or API calls with admin tokens.

## 1. Branch Protection Rules

Run the setup script with your GitHub PAT:

    export GITHUB_TOKEN=your_pat_here
    bash .github/scripts/setup-branch-protection.sh

This configures for cortex and ViralForge:
- Require 1 approving review before merge
- Require bandit and secret-scan status checks to pass
- Require branches to be up to date
- Block force pushes and deletions
- Enforce linear history
- Apply to administrators

Verify at: Settings > Branches > Branch protection rules

## 2. GitHub Pages

Navigate to: cortex repo > Settings > Pages
- Source: Deploy from a branch
- Branch: main
- Folder: /docs
- Save

Site will be available at: https://techknowmad-labs.github.io/cortex/

## 3. Enable Dependabot

Navigate to: Each repo > Settings > Code security and analysis
- Dependency graph: Enable
- Dependabot alerts: Enable
- Dependabot security updates: Enable
- Dependabot version updates: Enable (uses .github/dependabot.yml)

## 4. Enable Code Scanning (CodeQL)

Navigate to: Each repo > Settings > Code security and analysis
- Code scanning: Set up > Default
- Languages: Python
- Schedule: On push and weekly

Or push this workflow (.github/workflows/codeql.yml):

    name: CodeQL
    on:
      push:
        branches: [main]
      pull_request:
        branches: [main]
      schedule:
        - cron: '0 6 * * 1'
    jobs:
      analyze:
        runs-on: ubuntu-latest
        permissions:
          security-events: write
        steps:
          - uses: actions/checkout@v4
          - uses: github/codeql-action/init@v3
            with:
              languages: python
          - uses: github/codeql-action/analyze@v3

## 5. SAML Single Sign-On (Requires GitHub Enterprise Cloud)

GitHub Enterprise Cloud is required for SAML SSO.

If on Enterprise Cloud:
1. Navigate to: Org Settings > Authentication security
2. Enable SAML authentication
3. Configure with your IdP:
   - Sign on URL: (from your IdP)
   - Issuer: (from your IdP)
   - Public certificate: (from your IdP)
4. Supported IdPs: Okta, Azure AD, OneLogin, PingOne
5. Test the configuration before enforcing
6. Enable "Require SAML SSO authentication for all members"

If on Free/Team plan:
- SAML SSO is not available
- Use GitHub's built-in 2FA requirement instead:
  Org Settings > Authentication security > Require two-factor authentication

## 6. Organization Member Permissions

Navigate to: Org Settings > Member privileges

Recommended settings:
- Base permissions: Read (members can read all repos by default)
- Repository creation: Disabled for members (admins only)
- Repository forking: Private repos - disabled
- Pages creation: Public repos only
- Admin repository permissions:
  - Allow members to change repository visibilities: No
  - Allow members to delete or transfer repositories: No
  - Allow members to delete issues: No

## 7. Team Structure

Create teams at: Org Settings > Teams

Recommended structure:
- @TECHKNOWMAD-LABS/core — Admin access to all repos
- @TECHKNOWMAD-LABS/contributors — Write access to active repos
- @TECHKNOWMAD-LABS/security — Triage access + security alert visibility

Team permissions per repo:
| Team | cortex | ViralForge | .github |
|------|--------|------------|---------|
| core | Admin | Admin | Admin |
| contributors | Write | Write | Read |
| security | Triage | Triage | Read |

## 8. GitHub Discussions

Navigate to: cortex repo > Settings > Features
- Enable Discussions
- Create default categories:
  - Announcements (only maintainers can post)
  - Q&A (with answers)
  - Ideas
  - Show and Tell
  - General

## 9. Security Alerts and Notifications

Navigate to: Org Settings > Code security and analysis
- Enable for all repos:
  - Dependency graph
  - Dependabot alerts
  - Dependabot security updates
  - Secret scanning
  - Secret scanning push protection

Configure notifications:
- Org Settings > Notification routing
- Route security alerts to admin@techknowmad.ai

## 10. Audit Log and Compliance

Navigate to: Org Settings > Audit log
- Review authentication events monthly
- Export audit logs for compliance records
- Monitor for:
  - Failed login attempts
  - Permission changes
  - Repository visibility changes
  - Webhook modifications

## 11. GitHub Apps and OAuth

Navigate to: Org Settings > GitHub Apps
- Review installed apps quarterly
- Restrict third-party application access:
  Org Settings > Third-party access > Require approval

Recommended apps:
- Dependabot (built-in)
- CodeQL (built-in)
- Renovate (alternative to Dependabot for advanced config)

## 12. Webhooks

Navigate to: Org Settings > Webhooks
- Configure for CI/CD integration
- Use webhook secrets (never plain HTTP)
- Point to HTTPS endpoints only

## 13. Repository Rulesets (Modern Alternative to Branch Protection)

If available on your plan, rulesets provide more granular control:
Navigate to: Org Settings > Repository > Rulesets

Create ruleset "main-protection":
- Target: main branch across all repos
- Rules:
  - Restrict deletions
  - Require linear history
  - Require pull request (1 reviewer)
  - Require status checks (bandit, secret-scan, lint)
  - Block force pushes

## Verification Checklist

After completing setup, verify:
- [ ] Branch protection active on cortex main
- [ ] Branch protection active on ViralForge main
- [ ] Dependabot alerts enabled on all repos
- [ ] GitHub Pages serving at correct URL
- [ ] 2FA required for all org members
- [ ] Base member permissions set to Read
- [ ] Repository creation restricted to admins
- [ ] Discussions enabled on cortex
- [ ] Security notifications routing to admin email
- [ ] Third-party app access requires approval
