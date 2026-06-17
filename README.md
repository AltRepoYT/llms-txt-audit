# llms-txt-audit

`llms-txt-audit` is a small Python CLI and GitHub Action for validating `/llms.txt` files before they ship.

It checks whether your file follows the shape described by the official [llms.txt proposal](https://llmstxt.org/): a Markdown file with a project title, short summary, curated resource sections, and links to the pages an LLM should read for context.

Need to create the file first? Use the [AltRepo llms.txt Generator & Validator](https://altrepo.net/dev/llms-txt-generator.html) to draft a spec-shaped file, then use this CLI to protect it in CI.

## Why this exists

A useful `llms.txt` file is curated. It should not be a blind sitemap dump, and it should not contain `robots.txt` permission rules.

This tool helps teams catch common mistakes:

- missing project title
- missing blockquote summary
- no H2 resource sections
- no Markdown resource links
- `robots.txt` directives placed in `llms.txt`
- private-looking URLs such as `/admin`, `/account`, `/checkout`, or `/wp-admin`
- duplicate links
- links with no explanation
- relative links when absolute URLs are required

## Install

For local development from this repository:

```bash
python -m pip install -e .
```

After installation, the command is available as:

```bash
llms-txt-audit --help
```

You can also run it without installing by setting `PYTHONPATH`:

```bash
PYTHONPATH=src python -m llms_txt_audit.cli public/llms.txt
```

## Basic usage

Audit a local file:

```bash
llms-txt-audit public/llms.txt
```

Audit a directory that contains `llms.txt`:

```bash
llms-txt-audit public/
```

Audit a hosted file:

```bash
llms-txt-audit https://example.com/llms.txt
```

Discover `/llms.txt` from a site root:

```bash
llms-txt-audit https://example.com --discover
```

Print JSON for scripts or dashboards:

```bash
llms-txt-audit public/llms.txt --json
```

Use strict CI behavior:

```bash
llms-txt-audit public/llms.txt --strict --fail-on-warning
```

## Example output

```text
llms.txt audit: public/llms.txt

PASS  H1 title found. line 1
PASS  Blockquote summary found. line 3
PASS  3 H2 section(s) found.
PASS  4 Markdown resource link(s) found.
PASS  Optional section found.

Score: 100/100
Sections: 3  Links: 4  Optional: yes
```

## GitHub Action

Use the action from inside this repository:

```yaml
name: Validate llms.txt

on:
  pull_request:
  push:
    branches: [main]

jobs:
  llms-txt:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: ./llms-txt-audit
        with:
          target: public/llms.txt
          strict: "true"
          fail-on-warning: "true"
```

When this project is published as a standalone GitHub Action, replace `./llms-txt-audit` with the public action reference.

The action runs directly from `src`, so it does not need to build or install the package during the workflow.

## Action inputs

| Input | Default | Purpose |
| --- | --- | --- |
| `target` | `public/llms.txt` | Local path, directory, hosted `/llms.txt` URL, or site URL when `discover` is true. |
| `discover` | `false` | Treat `target` as a site root and audit `https://site.com/llms.txt`. |
| `strict` | `false` | Make recommended structure checks stricter. |
| `require-optional` | `false` | Warn when `## Optional` is missing. |
| `fail-on-warning` | `false` | Exit non-zero if warnings are found. |
| `no-relative-links` | `false` | Warn when resource URLs are relative. |

## Exit codes

| Code | Meaning |
| --- | --- |
| `0` | Audit completed without errors. |
| `1` | Audit found errors, or warnings when `--fail-on-warning` is enabled. |
| `2` | The target could not be read. |

## What this checks

### Required structure

A strong `llms.txt` file should start like this:

```md
# Project Name

> One short summary explaining what this site or project is.

Optional notes that help an LLM understand how to use the linked resources.

## Core
- [Overview](https://example.com/index.html.md): Project overview

## Docs
- [Quick start](https://example.com/docs/start.html.md): First setup path

## Optional
- [Sitemap](https://example.com/sitemap.xml): Complete canonical URL list
```

The audit checks for:

- one H1 title
- a blockquote summary
- H2 sections
- Markdown list links
- an optional `## Optional` section

### Link hygiene

The audit also flags:

- private-looking URLs
- duplicate URLs
- missing link descriptions
- unsupported URL schemes
- relative URLs when `--no-relative-links` is enabled

### robots.txt confusion

`llms.txt` is for context, not crawler permissions. If the file contains lines like this:

```txt
User-agent: *
Disallow: /admin
```

…the audit warns you to move those rules to `robots.txt`.

## What this does not do

This tool does not crawl your whole website or auto-generate a final curated file from every URL. That is intentional. A good `llms.txt` file should be selected by humans or documentation owners.

## Run tests

The test suite uses Python's standard library only:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

On Windows PowerShell:

```powershell
$env:PYTHONPATH='src'
python -m unittest discover -s tests -v
```
