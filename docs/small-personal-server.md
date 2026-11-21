# Guide: a small Personal server, starting from the reference server

Status: informative. Nothing here changes a requirement; where this guide and
[`SPEC.md`](../SPEC.md) disagree, `SPEC.md` wins.

This guide is for someone who wants to build a PCP server for one person and
has not read the whole specification. It starts from the
[reference server](../conformance/reference/server.py), shows what to keep,
gets a trimmed copy passing the [conformance suite](../conformance/README.md),
and then lists what the reference server leaves out and you must add before
you claim conformance (SPEC §10.3).

The reference server is a test fixture: one Python file, everything in
memory, no real consent screen, not for real data. Treat it as a map of the
protocol, not as a base for production.

## What a Personal server is

A **Personal context** is one person's context, controlled by that
person. A server serves it at one MCP endpoint, and an assistant connects to
that URL. Three things make it PCP rather than only an MCP server:

1. **Discovery.** A small JSON document that says what the context is and
   where everything else is.
2. **Authorization.** OAuth 2.1 as MCP defines it, with scopes that decide
   what each assistant can read or write.
3. **A fixed set of tools** over profile and memory, with defined behavior,
   so that any client can use any server.

Memory is a set of pages. A page is a Markdown body with YAML frontmatter at
a path such as `preferences/editor`.

## The smallest set

For a Personal context with a profile, the tools the suite looks for are
exactly these eight (TOOL-03):

| Tool | What it does | Scope it needs |
|---|---|---|
| `profile_get` | Read the profile | `profile.core:read` |
| `profile_update` | Change the profile with a JSON Merge Patch | `profile.core:write` |
| `memory_search` | Search pages | `memory:read` |
| `memory_read` | Read one page by path or id | `memory:read` |
| `memory_list` | List pages | `memory:read` |
| `memory_write` | Create or update a page | `memory:write` |
| `context_brief` | A short briefing to start a conversation | `profile.core:read` or `memory:read`; it never fails for a missing scope, it names what it left out |
| `audit_list` | The access log | `audit:read` |

The other standard tools (`memory_propose`, `review_list`, `review_resolve`,
`partition_list`) belong to the review and partition features, which a
Personal context does not need. `export_create` and `erase_request` are
optional tools, but see the end of this guide: a claim needs export.

The default grant for a Personal context is `profile.core:read memory:read
memory:write`. Everything else (`audit:read`, sensitive pages, `profile.core:write`)
is asked for separately, so an assistant that only needs to remember things
never holds more.

On the HTTP side, the smallest server answers these paths (all of them are in
the reference server's `Handler`):

| Path | Purpose |
|---|---|
| `/pcp/<context>/.well-known/pcp.json` | The context document (DISC) |
| `/.well-known/oauth-protected-resource/pcp/<context>/mcp` | Protected resource metadata (AUTH) |
| `/.well-known/oauth-authorization-server` | Authorization server metadata |
| `/oauth/authorize`, `/oauth/token`, `/oauth/revoke`, `/oauth/register` | OAuth |
| `/pcp/<context>/mcp` | The MCP endpoint |

You may serve the context document at `/.well-known/pcp.json` instead if the
server hosts one context (DISC-01).

## Step 1: get the code and the suite

From a checkout of this repository. Python 3.10 or later:

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r conformance/requirements.txt
```

Run the reference server and the suite once, so you know what a pass looks
like before you change anything:

```bash
conformance/run-reference.sh .venv/bin/python
```

It ends with `all mutation cases caught`. (That script also starts and stops
the server for you.)

## Step 2: copy the reference server and cut it down

Make a directory for your server and copy two things into it: the server file
and the schemas it validates tool input and output against.

```bash
mkdir mini && mkdir mini/schemas
cp conformance/reference/server.py mini/server.py
cp schemas/0.3/*.json mini/schemas/
```

Edit `mini/server.py` in two places.

**Where the schemas are.** The reference server finds them relative to this
repository. Replace

```python
ROOT = pathlib.Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "schemas" / "0.3"
```

with

```python
SCHEMAS = pathlib.Path(__file__).resolve().parent / "schemas"
```

**Which contexts it serves.** The reference server hosts three contexts, so
the suite can test work and team behavior too. A Personal server needs only
the first. In `CONTEXTS`, delete the `acme-dana` and `crew` entries so that
what is left reads

```python
CONTEXTS = {
    "dana": Context("dana", "personal", "human:dana", {"dana": "human:dana"}),
}
```

Run it, in one terminal:

```bash
cd mini
python3 server.py --port 8123 --test-mode
```

`--test-mode` makes the authorization endpoint approve at once for the user
named by `login_hint`, which is what lets the suite run without a person. A
real server shows a consent screen instead (see "What you must replace").

Look at what a client sees first. The context document:

```bash
curl -s http://127.0.0.1:8123/pcp/dana/.well-known/pcp.json
```

```json
{"pcp_version": "0.3", "kind": "personal", "controller_type": "human", "mcp_endpoint": "http://127.0.0.1:8123/pcp/dana/mcp", "resource_metadata": "http://127.0.0.1:8123/.well-known/oauth-protected-resource/pcp/dana/mcp", "authorization_server": "http://127.0.0.1:8123", "profile": "core", "export": false, "encryption": {"key_custody": "host", "readable_by": ["principals", "host"]}}
```

and what an unauthenticated call to the endpoint gets, which is how a client
learns where to authorize (AUTH):

```bash
curl -s -i -X POST http://127.0.0.1:8123/pcp/dana/mcp -H 'content-type: application/json' -d '{}'
```

```text
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Bearer resource_metadata="http://127.0.0.1:8123/.well-known/oauth-protected-resource/pcp/dana/mcp", scope="profile.core:read memory:read memory:write"
```

Note `"export": false` in the document: this server does not export yet, and
says so. A server must not claim what it does not do.

## Step 3: run the suite against it

In another terminal, from the repository root, with the same virtual
environment:

```bash
cd conformance
python3 -m pcp_conformance run --endpoint http://127.0.0.1:8123/pcp/dana/mcp \
  --allow-writes --allow-register --revocation-wait 10
```

`--allow-writes` writes test pages under `pcp-conformance/<run id>/`, and PCP
has no tool to delete pages, so use a throwaway context, as here. The result
for the trimmed server:

```text
96 pass, 0 fail, 0 warn, 25 skip, 78 manual or review (use -v to list)
```

Read the three groups that are not a pass:

- **skip**: a check that could not run. Each says why. Most are features this
  context does not use (partitions, review, connections, extensions) and are
  right to skip. Two need a second context of the same person
  (`--other-endpoint`; AUTH-25 and CTX-06). `KEY-05` and `KEY-07` apply under
  user custody only. `SEC-01` needs `--allow-load`. `TOOL-19` and `EXP-04`
  are skipped because `export_create` is not offered.
- **manual or review**: requirements of kind `M` and `R` in
  [`docs/conformance.md`](conformance.md) that a person checks, and `A`
  requirements that are checked on an export archive.
- **warn**: a SHOULD that is not met. A claim lists them, and they do not
  block it.

To work on one area, use `--only` with a requirement id, for example
`--only AUTH-25`. A check that cites several ids runs whole.

## Step 4: map the requirements to the work

The suite names a requirement id in every result, so a failure points at a
row of [`docs/conformance.md`](conformance.md) and from there at a section of
the specification. For a Personal server, in the order you will meet them:

| Area | Ids | What it asks of a small server |
|---|---|---|
| Discovery | `DISC` | The context document at the right URL, valid against its schema, with `pcp_version` `"0.3"` and the endpoint, authorization server and key custody it describes |
| Authorization | `AUTH` | Protected resource metadata, PKCE with S256 only, audience-bound tokens, a `401` that points to the metadata, client registration or client metadata documents, refresh and revocation, no tokens in URLs |
| Profile | `PROF` | A core profile that validates, and `profile_update` as a merge patch |
| Memory | `MEM` | Path rules, frontmatter, sensitivity and what the server stamps itself, and retrieval that honors lifecycle and sensitivity |
| Tools | `TOOL` | The eight tools above, with titles, annotations, output schemas, `structuredContent`, errors as results, `not_found` instead of `forbidden`, conflict on a stale `expected_updated` |
| Scopes | `SCOPE` | Sensitive memory behind its own scope |
| Grants and audit | `AUD` | A grant per assistant, and an audit entry for each access |
| Security | `SEC` | Origin and host checks, rate limiting, the `<memory_data>` framing of returned content, nothing listening on other addresses than intended |
| Custody and control | `KEY`, `CTX` | What the server says about who can read the data, and that a work or personal context never leaks into the other |

The reference server already does all of the `S` and `S+` rows for these
areas. When you replace a part of it, rerun the suite and the id that fails
tells you which row you broke.

## What you must replace

The reference server is deliberately missing, or fakes, four things. They are
the real work of a Personal server.

1. **Authorization approval.** In test mode the server approves every
   request. A real server shows the person a consent screen, naming the
   assistant and the scopes, and lets them approve or refuse (`AUTH`, and the
   `M` rows that a person checks on that screen). The suite cannot approve by
   itself against such a server: run it with `--interactive`, which prints an
   authorization URL for you to open and catches the redirect, or hand it a
   token with `--token`.
2. **Storage.** Pages live in a Python dict and are lost when the process
   ends. Store each page as a Markdown file with its YAML frontmatter (the
   examples are in [`examples/0.3/memory/`](../examples/0.3/memory/) and the
   rules in SPEC §5), keep the server-stamped keys out of the client's hands
   (MEM-09), and keep earlier versions if you want them exported under
   `history/`. The plain-file form is also what makes export simple.
3. **Export.** A Personal context that claims conformance must offer export
   (SPEC §10.3, item 4): discovery `export` is `true`, and an archive can be
   produced of everything the person can read (SPEC §8.1 to §8.6; the `EXP`
   ids). The suite checks an archive you give it:

   ```bash
   cd conformance
   python3 -m pcp_conformance archive ../examples/0.3/export/personal
   ```

   ```text
   ok   ../examples/0.3/export/personal: 11 files, hashes and counts check
   ```

   That example is a valid archive, and a good model of what your export must
   produce. Restoring an archive and exporting again must give the same
   archive (SPEC §8.8; the `IMP` ids), and restoring another implementation's
   archive is the proof PCP is for (SPEC §10.4).
4. **Persistence of the rest.** Grants, tokens, clients and the audit log are
   also in memory in the reference server. A real server keeps grants and
   the audit log across restarts, and must stop a revoked grant from working
   within the bound the specification gives (AUTH-28).

Two more are for your deployment rather than your code: TLS (the reference
server speaks plain HTTP on loopback only), and what you say about key
custody in discovery. Under `user` custody the host cannot read the data, and
the suite checks that with `--scan-path` (KEY-05).

## Step 5: what a conformance claim looks like

SPEC §10.3 says a server may list a profile in discovery `conformance` only
when, for that context:

1. every MUST that applies passes in a suite run against the same build,
   including the `S+` checks run with test data against a throwaway context
   (a check the suite skipped counts as an `M` requirement: it passes in a run
   that has the capability, or a person checks it);
2. every applicable `A` requirement passes on a full export of that context;
3. the `M` and `R` requirements that apply have been checked; and
4. discovery `export` is `true`.

A failed SHOULD does not prevent a claim. A claim you publish states the PCP
version, the profile, the suite version and the date of the run, where the
report can be read, how the `M` and `R` requirements were checked, and which
SHOULD requirements are not met. For example:

> *Implements PCP v0.3, Personal profile, for every context it hosts.
> Conformance suite 0.3.x, run on the date of the report (report linked).
> Management and review items checked by the maintainers; key custody
> evidence in the repository. Not met: the SHOULD requirements named in the
> report. Round trip verified with another implementation.*

Write your own with the real suite version, the real date, and a link to the
report from your own build, and list every SHOULD you miss. Do not put
`personal` in discovery `conformance` until all four conditions hold: the
suite can check a claim, and a claim it fails is a violation (SPEC §10.3).

## Where to go next

- Run the suite on every change: see the suite's
  [README](../conformance/README.md).
- If something in the specification or the suite was unclear while you built
  this, say so on the errata issue of this repository. A failed run that
  shows a gap is as useful as a pass.
- Read SPEC §5 (memory), §6 (tools), §3 (authorization) and §8 (export), in
  that order, once the trimmed server runs.
