# PCP Governance

PCP is an open protocol. This page says who decides what, and how. It is short on purpose while PCP is pre-1.0, and it will grow as more people take part.

## Principles

- **Open.** All work happens in public, in this repository's issues and pull requests.
- **Independent.** PCP belongs to no company or product. No implementation, the reference implementation included, has special standing.
- **Running code.** A proposal that comes with a working implementation, in any codebase, carries more weight.
- **Free to implement.** The spec, schemas and examples are Apache 2.0. Nobody needs permission to implement PCP.

## Roles

- **Contributors** are anyone who opens an issue, comments, or sends a pull request.
- **Maintainers** review and merge changes, publish releases, and keep the process fair. The maintainers are the owners of the [`pcp-protocol`](https://github.com/pcp-protocol) GitHub organization.

Any maintainer can nominate a contributor with a record of careful review or spec work. The nominee becomes a maintainer if no maintainer objects within 14 days. We want maintainers from more than one organization. Once there are four or more maintainers, no single organization should employ more than half of them.

Maintainers say so when a change they review mainly helps a product they work on.

## Proposing a spec change

1. **Open an issue.** Describe the problem, who it affects, and a rough idea of the fix. Typos, broken links and wording that does not change meaning can go straight to a pull request.
2. **Open a pull request** against `SPEC.md`, the schemas and the examples. Say whether it is **editorial** (no change in meaning) or **normative** (changes what implementations must or may do).
3. A normative pull request states what changes, what breaks, who is affected, and how to migrate. If a requirement changes, it also updates [`docs/conformance.md`](docs/conformance.md) and, where it can, the conformance suite.

## Deciding

- **Editorial changes** need one maintainer approval and can merge at any time.
- **Normative changes** stay open for comment for at least 14 days. They need approval from at least one maintainer who is not the author, and no unresolved objection from a maintainer. Silence after the comment period counts as agreement.
- **No agreement?** Maintainers first try to resolve it in the thread. If that fails, maintainers vote and a simple majority decides. The vote and the reasons are recorded in the pull request. A tie means the change does not go in.

Before v1.0, a release may break compatibility if it ships migration notes. From v1.0, a breaking change needs a new major version.

## Releases

- A release candidate is announced in an issue at least 14 days before it is tagged.
- Each version is tagged `vX.Y` and published as a GitHub release with notes on what changed.
- Conformance claims are checked against the spec and its suite. No one grants them.

## Changing this document

Changes to this page follow the rules for normative changes.
