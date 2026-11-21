# Running the suite in GitHub Actions

A workflow you can copy into your own repository. On every push and pull
request it installs the suite, starts your server, runs the suite against it,
and keeps the report as a build artifact, so a conformance claim (SPEC §10.3)
can link to a report from a real build.

The workflow file is [`ci/pcp-conformance.yml`](ci/pcp-conformance.yml). It
uses the one-command install described in the [suite README](README.md#install).

## Use it

1. Copy `ci/pcp-conformance.yml` to `.github/workflows/pcp-conformance.yml`
   in your repository.
2. Change the lines marked `CHANGE`:
   - `PCP_SUITE_REF`: the suite version to run, a tag or commit of
     `pcp-protocol/pcp`. Leave `main` while you build; pin a tag when you
     publish a claim, so the report names a fixed suite version.
   - `PCP_PROFILE`: `personal` or `team`.
   - `PCP_ENDPOINT`: the MCP endpoint your server serves in the job.
   - The "Start the server" step: the command that starts your server in the
     background.
3. Push. The report is under the run's **Artifacts** as
   `pcp-conformance-report`, as `pcp-report.json` and `pcp-report.md`. The
   report is kept even when the suite fails, and the job fails when any MUST
   fails (a warning for a SHOULD does not fail it).

## What your server needs for CI

- **A throwaway context with test data only.** The recipe runs with
  `--allow-writes`, which writes test pages under `pcp-conformance/<run id>/`.
  PCP has no tool to delete pages, so never point it at a context with real
  data.
- **Test approvals.** There is no person in CI to approve an authorization.
  The reference server has a `--test-mode` that approves at once for the user
  named by `login_hint`; give your server something equivalent for CI and
  keep it off in production. Checks that need an approval your server cannot
  give are reported as `skip`, and SPEC §10.3 says how skips count toward a
  claim.
- **Its own port.** The suite checks that the server does not also listen on
  other addresses of the machine (SEC-05). On a machine where something else
  already answers on that port on every address, that check fails for a
  reason that is not your server. Pick a port nothing else uses.

## What a green run does not cover

The recipe runs a single context with writes and client registration. It
does not run the checks that need more than that:

| To run | Add to the `pcp-conformance run` command |
|---|---|
| Audience binding and separation of two contexts (AUTH-25, CTX-06) | `--other-endpoint URL` for a second throwaway context of the same person |
| Team checks (partitions, review) | `--second-login NAME --private-partition P`, and `--profile team` |
| Delegation | `--delegated-token T` |
| Rate limiting (SEC-01) | `--allow-load`, against a test deployment only |
| Key custody under `user` custody (KEY-05) | `--scan-path DIR` for the server's data directory |

See the [options table](README.md#run-it) for every option. Requirements
marked `M` or `R` in [`docs/conformance.md`](../docs/conformance.md) and the
`A` requirements on an export archive are checked by a person, and a claim
says how.

## Checked against the reference server

This recipe was run step by step, in a clean environment, against the
[reference server](reference/server.py): install from a repository ref, start
the server in the background, wait for it, run the suite, collect the report,
stop the server. The run exited 0 with no failures, and wrote both report
files. The same repository's own CI runs the suite against the reference
server with [`run-reference.sh`](run-reference.sh).
