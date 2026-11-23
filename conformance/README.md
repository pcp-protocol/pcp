# PCP v0.3 conformance suite

Black-box checks of a PCP server against
[`docs/conformance.md`](../docs/conformance.md), which lists every
requirement of SPEC v0.3 with a stable id. Each result names the id it
checks, so a report reads as "AUTH-25 pass, SEC-10 fail" against the
document.

The suite checks what can be checked from outside: discovery, OAuth,
the MCP transport, the tool surface, scopes and leak tests with canary
strings, framing, audit entries, and export archives. Requirements that
need the management surface (`M`) or review evidence (`R`) are listed in
the report as manual; a conformance claim covers them by a person's check.

## Install

One command, from anywhere, with Python 3.10 or later:

```bash
pipx install "git+https://github.com/pcp-protocol/pcp"
```

or, in a virtual environment you already have, `pip install "git+https://github.com/pcp-protocol/pcp"`. Add `@<tag>` to pin the suite version a claim names. This installs the `pcp-conformance` command with the requirement list and the schemas it checks against bundled in, so it needs no checkout. To check JWE-encrypted export archives, add the `cryptography` package (an optional extra: `pip install "pcp-conformance[jwe] @ git+https://github.com/pcp-protocol/pcp"`).

Working from a clone instead, as before:

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r conformance/requirements.txt
```

The suite uses the standard library for HTTP and `jsonschema` and `pyyaml`
for the schemas in [`schemas/0.3/`](../schemas/0.3/).

## Run it

Against a server, writing a report a claim can link to:

```bash
pcp-conformance run --endpoint https://ctx.example.com/mcp --profile personal --report-dir report
```

From a clone, in the `conformance/` directory, the same suite runs as
`python3 -m pcp_conformance run ...` with the same options.

By default the suite is **read-only**: it fetches discovery and metadata,
sends unauthenticated and invalid requests, and registers nothing. Checks
that need more say so and are skipped. Widen it with:

| Option | What it allows |
|---|---|
| `--interactive` | Run OAuth in your browser: the suite prints an authorization URL and catches the redirect on a loopback port. Each scope set the checks need is one approval. |
| `--token T [--token-scopes "a b"]` | Use an access token you already have, instead of OAuth. Checks that need other scopes are skipped. |
| `--allow-register` | Register OAuth clients and check the DCR rules, and probe the CIMD fetcher with addresses it must refuse (it should never fetch them). `--interactive` and `--allow-writes` also register the one client they need, but only this flag runs the registration and CIMD checks. |
| `--allow-writes` | Write test pages. Every page lives under `pcp-conformance/<run id>/` (one under `style/`, for the §5.7 default) and carries a unique canary string. **Use a throwaway context** and delete the context afterwards: no required PCP tool deletes pages. If the server offers `erase_request`, that removes them too. |
| `--allow-load` | Send a burst of bad token requests to check rate limiting (SEC-01). Only against a test deployment. |
| `--other-endpoint URL` | A second context of the same person, for audience binding (AUTH-25) and separation (CTX-06). With `--allow-writes` the suite writes one canary page into it too, so it must also be a throwaway context. |
| `--second-token T` or `--second-login NAME`, `--private-partition P` | A second principal and a partition it cannot read, for the team checks. |
| `--delegated-token T` | An agent token acting for a human, for the delegation checks. |
| `--scan-path DIR` | The server's data directory. Under `user` custody the suite writes a canary and searches every file for it (KEY-05). |
| `--revocation-wait S` | How long to wait for a revoked grant to stop working (default 300, the SPEC's bound). |
| `--only IDS` | Run only the checks that cite these ids. A check that cites several ids runs whole, so the report can list ids you did not name. |
| `--profile personal\|team` | The profile the run is for, written into the report. Without it the report uses the server's own claim when it names exactly one profile, else `unspecified`. |
| `--json` | Print the report to standard output as JSON instead of the readable list. |
| `--report FILE`, `--report-md FILE`, `--report-dir DIR` | Write the JSON report, the Markdown report, or both (`DIR/pcp-report.json` and `DIR/pcp-report.md`). The report is written even when a check fails. |

Give the server a port nothing else on the machine uses: the loopback check (SEC-05) connects to the machine's other addresses on that port, and cannot tell your server from another program that answers there.

The exit status is 1 if any MUST failed. A failed SHOULD is a warning. A
skipped check is not a pass: SPEC §10.3 says how skipped requirements count
toward a claim.

### Archives

```bash
python3 -m pcp_conformance archive context.pcp.zip            # SPEC §8.3 checks
python3 -m pcp_conformance roundtrip a.pcp.zip b.pcp.zip       # SPEC §8.8, same implementation
python3 -m pcp_conformance roundtrip a.pcp.zip b.pcp.zip --cross   # across implementations
```

`archive` unpacks safely (it refuses absolute paths, `..`, links and
repeated names, as an importer must) and runs the same checks as
[`scripts/validate_schemas.py`](../scripts/validate_schemas.py). Pass
`--keys` with a JSON key file to check file-level JWE content.

## The report

The JSON report records the suite name and version, the PCP version (`spec_version`), the profile, the date and time of the run, the endpoint, the options used (tokens are never written), and one entry per requirement id in `docs/conformance.md` under `requirements`. Each entry has the id, level, section, the profile column, how it is checked, and its `status`:

| Status | Meaning |
|---|---|
| `pass` | Checked and met. |
| `fail` | A MUST was not met. The exit status is 1. |
| `warn` | A SHOULD was not met. |
| `skip` | The check did not run. `skip_kind` says why: `not_applicable` when the context does not use the feature (for example partitions or review), `not_run` when the run lacked an option, a token or an approval. A `not_run` skip is not a pass: SPEC §10.3 says it still has to pass in another run or be checked by a person. The readable output shows the first kind as `N/A` and the second as `SKIP`. |
| `manual` | Not checkable from outside (`M`, `R`, and `A` requirements); a person checks it. |

`requirement_summary` counts the entries by status, and `skipped` counts the skips of each kind. `notices` lists what a reader must know that no single requirement says: for example that discovery `export` is not `true`, so no claim is possible from the run (SPEC §10.3 item 4). The older `findings` list, one row per check result, is still written. The Markdown report holds the same header, the counts, every failure, warning and skip with its message, and the ids that passed, so it can be linked from a claim or attached to a build. A claim links the report and names the same suite version, PCP version and profile.

## The reference server

[`reference/server.py`](reference/server.py) is a small PCP server, in memory
and in one file, that exists so the suite can run in CI. It is not for real
data. It serves three contexts on `127.0.0.1`: a personal one, a work one
controlled by an organization, and a team one with partitions and review.
In `--test-mode` it approves authorizations at once for the user named by
`login_hint`.

```bash
conformance/run-reference.sh .venv/bin/python
```

runs the self-check, the suite against all three contexts, and then the
suite against four deliberately broken builds of the server
(`--break sensitive-leak`, `audience`, `origin`, `framing`), each of which
must make the suite fail on the requirement it breaks. CI runs the same
script.

## In CI

[`github-actions.md`](github-actions.md) has a workflow file to copy into your
own repository: it installs the suite, starts your server, runs the suite and
keeps the report as a build artifact.

## Coverage rules

```bash
python3 -m pcp_conformance self-check
```

fails when a requirement marked `S` or `S+` in `docs/conformance.md` has no
check, when a check cites an id the document does not have, or when a
standard tool (SPEC §6.2) has no check that calls it. Add a requirement to
the document and the self-check tells you to write its check.

## Claiming conformance

SPEC §10 says what a claim states. In short: the profile, the suite version
and date, the report, and how the manual and review items were checked.
