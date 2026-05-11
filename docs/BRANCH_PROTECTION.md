# Branch Protection

Use the `main` branch as the protected default branch.

Recommended GitHub rules:
- Require a pull request before merging
- Require approvals: 1 or 2, depending on team size
- Require status checks to pass before merging
- Require the `CI / lint-and-test` check
- Require branches to be up to date before merging
- Restrict force pushes
- Restrict deletions

The required check comes from the GitHub Actions workflow in [`.github/workflows/ci.yml`](../.github/workflows/ci.yml).

If you want, I can also add a stronger CI matrix for linting, formatting, and mobile/backend jobs.