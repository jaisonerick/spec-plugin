---
name: cloudflare-dns
description: >-
  Manage Cloudflare DNS zones and records via Terraform in nexaedge/infrastructure.
  Auto-invoke when configuring a new domain, subdomain, DNS record, or zone.
  TRIGGER when: user mentions "DNS", "domain", "subdomain", "A record", "CNAME",
  "MX record", "TXT record", "SPF", "DKIM", "DMARC", "nameserver", "zone",
  "cloudflare", or needs to point a domain/subdomain to a service, IP, or Pages project.
  DO NOT TRIGGER when: user is asking about DNS concepts without wanting to make changes,
  or when working on non-NexaEdge infrastructure.
argument-hint: "<domain-or-subdomain> [record-type] [target]"
---

# Cloudflare DNS Management Skill

You manage DNS zones and records for NexaEdge domains through Terraform — never through the Cloudflare dashboard or CLI.

## Constraints

- **NEVER run Cloudflare CLI commands or API calls directly.** All DNS changes go through Terraform.
- **NEVER run `terraform plan` or `terraform apply` locally.** All Terraform operations go through GitHub Actions via PR.
- **NEVER create `aws_iam_access_key` resources.** GitHub Actions uses OIDC federation.
- All changes are made in the `nexaedge/infrastructure` repository under the `cloudflare/` stack.

## Infrastructure Repository

- **Path**: `~/code/nexaedge/infrastructure`
- **Cloudflare stack**: `~/code/nexaedge/infrastructure/cloudflare/`
- **DNS zones and records**: `~/code/nexaedge/infrastructure/cloudflare/zone.tf`
- **Pages projects and domains**: `~/code/nexaedge/infrastructure/cloudflare/pages.tf`
- **HTTP redirect rules**: `~/code/nexaedge/infrastructure/cloudflare/redirects.tf`

## Workflow

Follow these phases in order. Do NOT skip phases.

### Phase 1: Understand the Request

Clarify what the user needs:
- **New zone** (entire domain) or **new record** (subdomain/record on existing zone)?
- What **record type**? (A, AAAA, CNAME, MX, TXT, etc.)
- What **target/content**? (IP address, hostname, text value, etc.)
- Should it be **proxied** through Cloudflare? (orange cloud — default yes for web traffic, no for MX/TXT)
- Any **TTL preference**? (default: 1 = automatic when proxied, 300 for non-proxied)
- Does it need **email authentication** records? (SPF, DKIM, DMARC)

If the request comes from another skill/agent with enough context, proceed without asking.

### Phase 2: Read Current State

1. Navigate to the infrastructure repo and read current DNS configuration:

```bash
cd ~/code/nexaedge/infrastructure
git checkout main
git pull --rebase
```

2. Read the relevant Terraform files:
   - Always read `cloudflare/zone.tf` to see existing zones and records
   - Read `cloudflare/pages.tf` if the domain points to a Cloudflare Pages project
   - Read `cloudflare/redirects.tf` if the domain needs redirect rules
   - Read `cloudflare/outputs.tf` to see what nameserver outputs exist

3. Identify if the zone already exists or needs to be created.

### Phase 3: Write Terraform Changes

Create a new branch and make changes:

```bash
cd ~/code/nexaedge/infrastructure
git checkout -b dns/<descriptive-branch-name>
```

#### Adding a New Zone

Add to `cloudflare/zone.tf`. Follow existing patterns exactly:

```hcl
resource "cloudflare_zone" "<domain_identifier>" {
  account = {
    id = var.cloudflare_account_id
  }
  name = "example.com"
  type = "full"
}
```

**Naming convention**: Replace dots with underscores, remove TLD separators. Examples:
- `nexaedge.com` → `nexaedge_com`
- `nexaedge.com.br` → `nexaedge_com_br`
- `example.dev` → `example_dev`

When adding a new zone, also add nameserver outputs in `cloudflare/outputs.tf`:

```hcl
output "cloudflare_nameservers_<domain_identifier>" {
  value = cloudflare_zone.<domain_identifier>.name_servers
}
```

#### Adding DNS Records

Add to `cloudflare/zone.tf` grouped with the zone's other records. Follow existing patterns:

```hcl
resource "cloudflare_dns_record" "<zone>_<name>_<type>" {
  zone_id = cloudflare_zone.<zone>.id
  name    = "subdomain"    # Use the subdomain part, or "@" for apex
  type    = "CNAME"        # A, AAAA, CNAME, MX, TXT, etc.
  content = "target.example.com"
  ttl     = 1              # 1 = automatic (when proxied), 300 for non-proxied
  proxied = true           # true for web traffic, false for MX/TXT/non-HTTP
}
```

**Resource naming convention**: `<zone_identifier>_<record_description>_<type>`
- Examples: `nexaedge_com_www_cname`, `nexaedge_com_mx`, `nexaedge_com_spf_txt`

**Common record patterns from existing config:**

CNAME to Cloudflare Pages:
```hcl
resource "cloudflare_dns_record" "<zone>_<sub>_cname" {
  zone_id = cloudflare_zone.<zone>.id
  name    = "subdomain"
  type    = "CNAME"
  content = "${cloudflare_pages_project.<project>.name}.pages.dev"
  ttl     = 1
  proxied = true
}
```

MX record (Google Workspace):
```hcl
resource "cloudflare_dns_record" "<zone>_mx" {
  zone_id  = cloudflare_zone.<zone>.id
  name     = "@"
  type     = "MX"
  content  = "smtp.google.com"
  ttl      = 300
  priority = 1
}
```

SPF record:
```hcl
resource "cloudflare_dns_record" "<zone>_spf_txt" {
  zone_id = cloudflare_zone.<zone>.id
  name    = "@"
  type    = "TXT"
  content = "v=spf1 include:_spf.google.com -all"
  ttl     = 300
}
```

DMARC record:
```hcl
resource "cloudflare_dns_record" "<zone>_dmarc_txt" {
  zone_id = cloudflare_zone.<zone>.id
  name    = "_dmarc"
  type    = "TXT"
  content = "v=DMARC1; p=reject; rua=mailto:dmarc@example.com"
  ttl     = 300
}
```

Amazon SES verification:
```hcl
resource "cloudflare_dns_record" "<zone>_ses_mx" {
  zone_id  = cloudflare_zone.<zone>.id
  name     = "@"
  type     = "MX"
  content  = "feedback-smtp.sa-east-1.amazonses.com"
  ttl      = 300
  priority = 10
}
```

#### Adding Cloudflare Pages Domain Bindings

If the domain should serve a Cloudflare Pages project, add to `cloudflare/pages.tf`:

```hcl
resource "cloudflare_pages_domain" "<project>_<domain_desc>" {
  account_id   = var.cloudflare_account_id
  project_name = cloudflare_pages_project.<project>.name
  domain       = "subdomain.example.com"
}
```

#### Adding Redirect Rules

If the domain needs HTTP redirects (e.g., www → apex, or alias domain → primary), add to `cloudflare/redirects.tf`:

```hcl
resource "cloudflare_ruleset" "<zone>_redirects" {
  zone_id = cloudflare_zone.<zone>.id
  name    = "<domain> redirects"
  kind    = "zone"
  phase   = "http_request_dynamic_redirect"

  rules = [
    {
      action = "redirect"
      action_parameters = {
        from_value = {
          status_code = 301
          target_url = {
            expression = "concat(\"https://target.example.com\", http.request.uri.path)"
          }
        }
      }
      expression  = "(http.host eq \"source.example.com\")"
      description = "Redirect source.example.com to target.example.com"
      enabled     = true
    }
  ]
}
```

### Phase 4: Commit and Push PR

1. Stage only the changed Terraform files:

```bash
cd ~/code/nexaedge/infrastructure
git add cloudflare/zone.tf cloudflare/outputs.tf  # and any other changed files
git commit -m "dns: add <description of what was added>"
git push -u origin dns/<branch-name>
```

2. Create a PR:

```bash
gh pr create --title "dns: <short description>" --body "$(cat <<'EOF'
## Summary
- <what DNS changes were made>

## Terraform Changes
- <list of resources added/modified>

## Verification
After apply, verify records with:
```
dig <domain> <record-type>
```
EOF
)"
```

3. Tell the user the PR was created and that GitHub Actions will run `terraform plan`.

### Phase 5: Review Plan

1. Wait for the plan to complete:

```bash
gh pr checks <pr-number> --repo nexaedge/infrastructure --watch
```

2. Read the plan output from PR comments:

```bash
gh api repos/nexaedge/infrastructure/pulls/<pr-number>/comments --jq '.[].body' | tail -1
```

3. Present the plan summary to the user:
   - Resources to be created/modified/destroyed
   - Any unexpected changes
   - Ask for confirmation to proceed

If the plan shows errors or unexpected changes, help the user fix them (go back to Phase 3).

### Phase 6: Merge PR

Once the user confirms the plan looks good:

```bash
gh pr merge <pr-number> --repo nexaedge/infrastructure --squash --delete-branch
```

This triggers the `terraform-apply` workflow on the `main` branch.

### Phase 7: Watch Apply

Monitor the apply workflow:

```bash
# Find the latest workflow run
gh run list --repo nexaedge/infrastructure --workflow terraform-apply.yml --limit 1

# Watch it
gh run watch <run-id> --repo nexaedge/infrastructure
```

If the apply fails, read the logs and help debug:

```bash
gh run view <run-id> --repo nexaedge/infrastructure --log-failed
```

### Phase 8: Verify DNS Records

After successful apply, verify the DNS records are live:

```bash
dig <domain> <record-type> +short
```

For new zones, also output the nameservers the user needs to configure at their registrar:

```bash
dig <domain> NS +short
```

Tell the user:
- What records are now live
- If it's a new zone: the nameservers they need to set at their domain registrar
- DNS propagation may take up to 48 hours for new zones, but typically completes in minutes for record changes on existing zones

## Important Notes

- **Proxied records** (orange cloud): Cloudflare acts as reverse proxy — hides origin IP, provides CDN/WAF. Use for web traffic (HTTP/HTTPS). TTL is automatic (set to 1).
- **DNS-only records** (gray cloud): Direct DNS resolution. Use for MX, TXT, non-HTTP services. Set explicit TTL (typically 300).
- **Email records** are never proxied: MX, SPF (TXT), DKIM (TXT/CNAME), DMARC (TXT).
- **Cloudflare provider version**: `~> 5.0` — check the provider docs if unsure about resource schema.
- When adding a domain that will host a website, you likely also need a Pages project in `pages.tf` and possibly redirect rules in `redirects.tf`.
