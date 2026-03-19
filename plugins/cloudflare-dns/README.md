# Cloudflare DNS Plugin

Manage Cloudflare DNS zones and records through Terraform in the `nexaedge/infrastructure` repository.

## What it does

This skill automates the full DNS management workflow:

1. Reads current DNS state from Terraform files
2. Writes zone/record changes following existing patterns
3. Commits and opens a PR on `nexaedge/infrastructure`
4. Reviews the `terraform plan` output from GitHub Actions
5. Merges the PR to trigger `terraform apply`
6. Watches the apply workflow until completion
7. Verifies DNS records are live

## Auto-invocation

This skill is automatically invoked when you mention domains, subdomains, DNS records, zones, or Cloudflare DNS configuration for NexaEdge infrastructure.

## Constraints

- All DNS changes go through Terraform — never through Cloudflare CLI, API, or dashboard
- `terraform plan` and `terraform apply` only run in GitHub Actions, never locally
- Changes follow the existing patterns in `cloudflare/zone.tf`, `cloudflare/pages.tf`, and `cloudflare/redirects.tf`
