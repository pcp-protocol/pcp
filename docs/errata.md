# PCP v0.3 errata

Status: informative. This page lists wording in [`SPEC.md`](../SPEC.md),
[`docs/conformance.md`](conformance.md) and the
[conformance suite](../conformance/) that implementers found unclear,
inconsistent or unsafe to read literally. It changes no requirement. Where
this page and `SPEC.md` disagree, `SPEC.md` wins.

## How this page works

- **Report.** Comment on the
  [errata issue](https://github.com/pcp-protocol/pcp/issues/39) with the
  section, the text, and what you thought it meant. A failed suite run that
  shows a gap is as useful as a pass.
- **List.** Maintainers add each report here with an id (`E-01`, `E-02`,
  ...). An id is never reused.
- **Fix.** Items that only need clearer wording are grouped into editorial
  pull requests. An item that changes what a server or client must do is not
  fixed here: it moves to its own issue, labelled `normative`, and follows
  the comment period in [`GOVERNANCE.md`](../GOVERNANCE.md).

Each item has one of these states:

| State | Meaning |
|---|---|
| Open | Reported. No reading has been agreed yet. |
| Fix proposed | A pull request with the fix is open and linked. |
| Fixed | The fix is merged. The item stays listed so older copies can be checked against it. |
| Moved | The item changes meaning and is handled in the linked issue or pull request. |

## At a glance

| Id | Where | Short description | State |
|---|---|---|---|
| [E-01](#e-01) | SEC-05, suite | The check can fail because of another process on the test machine | Fix proposed |
| [E-02](#e-02) | Suite README, `--only` | A check that cites several ids runs whole | Fix proposed |
| [E-03](#e-03) | SPEC §10.3, suite report | One id can have more than one result in a run | Open |
| [E-04](#e-04) | SPEC §10.3, suite report | Two kinds of skip read the same | Fix proposed |
| [E-05](#e-05) | SPEC §10.3, `docs/conformance.md` | A run does not know which profile it is for | Open |
| [E-06](#e-06) | Suite README, `--allow-writes` | No required tool can remove the suite's test pages | Fix proposed |
| [E-07](#e-07) | SPEC §10.3 item 4, suite | A run with `export` set to `false` can look clean | Fix proposed |
| [E-08](#e-08) | SPEC §9.1.4 | `device` custody does not say who approves a grant | Moved |

## Items

### E-01

**SEC-05 depends on the test machine.** The check connects to the machine's
other addresses on the server's port. Where an unrelated service already
listens on that port on every address, SEC-05 fails although the server
under test binds loopback only. The requirement does not say how the suite
tells the server's own listener from another process, or that the port must
be free of other listeners.

Until this is settled: run the suite on a machine where nothing else listens
on the server's port, and say so in the report if SEC-05 was checked another
way.

State: Fix proposed in [#103](https://github.com/pcp-protocol/pcp/pull/103). The failure message now says that another program may be answering, and the suite README says to give the server a port nothing else uses.

### E-02

**A check that cites several ids runs whole.** `--only DISC-01` also runs
and reports DISC-12 and DISC-14, because one check cites all three. The
suite README says `--only` runs "the checks that cite these ids", which is
accurate, but a reader can expect only the named ids in the report.

State: Fix proposed in [#103](https://github.com/pcp-protocol/pcp/pull/103), which adds that sentence to the options table of the suite README.

### E-03

**One id can have more than one result in a run.** Several checks can cite
the same id, so one check can pass it while another skips it. The suite
report keeps one entry per id with a single status, worst first: fail, warn,
pass, skip, manual. SPEC §10.3 does not say how a mixed result for one id
counts toward a claim.

State: Open.

### E-04

**Two kinds of skip read the same.** A check is skipped when the context
does not use a feature (for example partitions or review), and also when the
run lacked an option (for example `--other-endpoint` or
`--delegated-token`). Both show as `SKIP`. SPEC §10.3 item 1 treats only the
second kind as something that still has to pass in another run or be checked
by a person. A reader of a report cannot tell them apart without reading
each message.

Until this is settled: a published claim should say, for every skipped id,
which kind of skip it was.

State: Fix proposed in [#103](https://github.com/pcp-protocol/pcp/pull/103). The report marks each skip as not applicable or not run, and SPEC §10.3 item 1 says that only the second kind needs anything further.

### E-05

**A run does not know which profile it is for.** The suite does not take or
verify a profile, and applies every check whose conditions it finds. The
`Profile` column of [`docs/conformance.md`](conformance.md) is not used to
choose checks, so a report for a Personal server still lists team-only ids
as skipped. SPEC §10.3 says a claim covers "every MUST of the profile that
applies", and nothing says where that list comes from for a run.

State: Open.

### E-06

**No required tool can remove the suite's test pages.** With
`--allow-writes` the suite writes test pages and tells the person to remove
them "with erasure". `erase_request` is optional, so a Personal server
without it has no way to clean up through the protocol.

Until this is settled: run write checks against a throwaway context, as SPEC
§10.3 item 1 already asks for the `S+` checks.

State: Fix proposed in [#103](https://github.com/pcp-protocol/pcp/pull/103). The suite README now says to delete the throwaway context afterwards, and that `erase_request` also works where a server offers it.

### E-07

**A run with `export` set to `false` can look clean.** A Personal server
that sets discovery `export` to `false` skips TOOL-19 and EXP-04 and still
shows a run with no failures. SPEC §10.3 item 4 requires `export` to be
`true` for a claim, and the suite does not flag that a claim is not possible
while it is `false`.

Until this is settled: a clean report is not enough for a claim on its own.
Check §10.3 item 4 by hand.

State: Fix proposed in [#103](https://github.com/pcp-protocol/pcp/pull/103). The report says in a note at the top that no claim is possible while `export` is not `true`.

### E-08

**`device` custody does not say who approves a grant.** In SPEC §9.1.4, V1
to V4 say where keys and plaintext live, but not who approves a grant. A
server could declare `device` while an authorization server run by the host
issues tokens that the device runtime accepts. The host could then register
a client, approve it and receive plaintext through the relay, so V1 would be
false while V1 to V4 still read as met.

This changes what a server must do, so it is not an editorial fix. The rule
is proposed as V5 in
[#89](https://github.com/pcp-protocol/pcp/pull/89): a grant takes effect
only once a principal approves it on one of their devices, the runtime
verifies every token, and a token the host can issue on its own unlocks
nothing.

Until that is merged: anyone who declares `device` custody under v0.3 should
apply the same rule. Without it the declaration does not hold.

State: Moved to [#89](https://github.com/pcp-protocol/pcp/pull/89).
