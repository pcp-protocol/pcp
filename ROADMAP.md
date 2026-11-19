# PCP Roadmap

Where PCP is going, milestone by milestone, and where you can help.

This page has milestones and no dates. A version ships when its "done when"
is met, and the more people build, the sooner that is. Scope is decided in
public issues and pull requests, as [`GOVERNANCE.md`](GOVERNANCE.md)
describes, and anyone can propose a change to this page (see
[Changing this roadmap](#changing-this-roadmap)).

## At a glance

| Milestone | Theme | State |
|---|---|---|
| [v0.3](https://github.com/pcp-protocol/pcp/releases/tag/v0.3) | The first version independent implementations can build against | Released |
| [v0.3.x](#v03x-prove-it) | Prove it: first conformance claims, first round trip between two implementations | In progress |
| [v0.4](#v04-connections) | Connections: a context's links to other services, made safe and checkable | Issues open, help wanted |
| [v0.5](#v05-trust-you-can-check) | Trust you can check: signatures, stronger tokens, a standard management surface, a client profile | Open for proposals |
| [v0.6](#v06-between-contexts) | Between contexts: sharing, moving hosts without reconnecting, merging | Open for ideas |
| [v1.0](#v10-stable) | Stable: a compatibility promise | Criteria drafted |

## Where PCP stands today

- The specification is at v0.3, request for comments: 14 standard tools,
  three context kinds, export and import with a checkable archive,
  authorization for current MCP, and defined key custody.
- A conformance suite checks a server against 197 requirements, and a
  reference server passes it in CI on every change.
- **No implementation claims conformance yet, and no archive has made a
  round trip between two independent implementations.** SPEC §10.4 says
  that round trip is the only test of what PCP is for. That is why the next
  step is proof, not new features.
- One maintainer so far. [`GOVERNANCE.md`](GOVERNANCE.md) wants maintainers
  from more than one organization, and this roadmap is partly an invitation.

## How versions work

- Milestones are an order, not a calendar. Work on a later milestone can
  start at any time and does not wait for the one before it. Whatever is
  ready, with running code, goes into the next release.
- Before v1.0, a v0.x release may break compatibility, and always ships
  migration notes. From v1.0, a breaking change needs a new major version.
- Editorial fixes merge at any time. Normative changes stay open for comment
  for at least 14 days, and a release candidate is announced at least 14
  days before a tag.
- A change with running code, in any codebase, carries more weight than one
  without. A requirement nobody has implemented can wait for the next
  version.
- Each version below has a milestone in the issue tracker. The milestone,
  not this page, is the list of what is in.

## v0.3.x: Prove it

**Goal:** show that v0.3 works between implementations that do not share
code. No normative changes.

- **First conformance claims.** At least one Team claim and one Personal
  claim, each with a public suite report, as SPEC §10.3 describes.
- **First cross-implementation round trip.** Two implementations restore
  each other's export (SPEC §8.8, IMP-08), with both archives and both
  reports published.
- **An interop table in this repository:** which implementation has restored
  whose archive, with the versions and dates.
- **A suite that is easy to run:** installable with one command, a report
  file a claim can link to, clearer notes for the interactive mode, and a CI
  recipe an implementation can copy.
- **Errata.** Wording that real implementations found unclear, fixed as
  editorial changes.
- **Guides:** building a small Personal server from the reference server,
  and connecting a client.
- **Schemas in a public schema registry**, in addition to this repository's
  pages (SPEC §11).

**Done when:** two codebases have published claims, and one round trip
between them is public.

**Help wanted:** run the suite against anything you have built and open an
issue with what was unclear. A failed run that shows a gap in the
specification is as useful as a pass. Claims from implementations that
share no maintainer with this repository are the strongest evidence.

## v0.4: Connections

**Goal:** a connection is a context's link to another service, such as a
mailbox, a calendar or a notes app. v0.3 names connections and reserves
their scopes, and leaves most of their behavior open. v0.4 closes that, and
takes in what the first implementers learned.

Connections:

- Public discovery does not reveal which services a person linked
  ([#20](https://github.com/pcp-protocol/pcp/issues/20)).
- What a server does with a scope for a connection that is not there
  ([#21](https://github.com/pcp-protocol/pcp/issues/21)).
- Two accounts of the same service, and stable connection ids
  ([#22](https://github.com/pcp-protocol/pcp/issues/22)).
- An error code for a connection that needs the person's attention
  ([#23](https://github.com/pcp-protocol/pcp/issues/23)).
- Tool titles and descriptions are written by the host, not passed on from
  the connected service
  ([#25](https://github.com/pcp-protocol/pcp/issues/25)).
- Copies a host keeps of connection data count as content, for encryption,
  export and erasure
  ([#26](https://github.com/pcp-protocol/pcp/issues/26)).
- A schema for connections in an export archive
  ([#27](https://github.com/pcp-protocol/pcp/issues/27)).
- One vocabulary: connection, source, client
  ([#28](https://github.com/pcp-protocol/pcp/issues/28)).
- A contract for how connection data enters a context: fetched live, or
  synced and kept (SPEC §11).

Import, memory and management:

- Reference imports, so that a bulk import from another tool does not become
  hundreds of proposals to review
  ([#17](https://github.com/pcp-protocol/pcp/issues/17)).
- Narrowing a grant without a new consent, in the informative management API
  ([#24](https://github.com/pcp-protocol/pcp/issues/24)).
- A decision on memory conflicts: are `relations` enough, or does a server
  need a merge and supersession rule (SPEC §11)?
- A decision on pages that belong to several partitions (SPEC §11).

Extensions:

- Schemas for the five reserved profile namespaces: `pcp.residency`,
  `pcp.legal`, `pcp.family`, `pcp.finance` and `pcp.home`. One pull request
  each. Domain knowledge matters more here than protocol knowledge.
- The shared documents and handoffs slots, registered by the implementers
  who need them (SPEC §6.5).

Conformance:

- A requirement family for connections, suite 0.4, and migration notes from
  v0.3.

**Done when:** every issue in the milestone is closed or moved with a
reason, the suite passes on the reference server, and each new requirement
has been run by at least one real implementation.

**Help wanted:** if you build connectors, or run a service that hosts them,
comment on the connection issues. The namespace schemas are a good first
contribution to the specification.

## v0.5: Trust you can check

**Goal:** make more of PCP's promises verifiable by someone who does not
trust the host.

- **Signed archives:** signed manifests or detached signatures, so an
  archive proves where it came from (SPEC §8.3, §11).
- **Stronger tokens:** sender-constrained tokens (DPoP), and per-partition
  grants carried in OAuth (RFC 9396) (SPEC §11).
- **A standard management surface.** Today
  [`docs/management-api.md`](docs/management-api.md) is an informative
  draft. As an optional profile with requirements, a person could manage
  grants, keys, export and erasure on any host with the same tool.
- **A client profile.** Every requirement today is on servers. A conforming
  client would show the context's kind at consent, treat returned content as
  data and not as instructions, handle step-up, and survive error codes it
  does not know. It comes with a test harness: a mock server that a client
  is run against.
- **A host profile:** for anyone who hosts contexts for other people, with
  tenant isolation and a defined form for the evidence behind review-only
  requirements.
- **Custody:** a value for runtimes in attested enclaves that the operator
  cannot read, and guidance on searchable encryption (SPEC §9.1, §11).
- **An independent security review** of the specification and the threat
  model in [`SECURITY.md`](SECURITY.md). We are looking for reviewers, and
  for a sponsor if a paid review is the only way to get one.

**Help wanted:** security engineers, OAuth people, anyone who operates
enclaves, and client authors. This version needs the most outside eyes.

## v0.6: Between contexts

**Goal:** contexts that work with each other, and a move between hosts that
nobody else notices.

- **Sharing between contexts:** one context shares scoped content with
  another (inside a family, from a person to a team, across the work and
  personal line), with consent, audit on both sides and revocation
  (SPEC §11, federation).
- **Moving without reconnecting.** Switching hosts is export plus import
  today, and then every client has to be connected again. Open questions: a
  signed notice that a context has moved, how grants follow it, and context
  addresses on a domain the person owns.
- **Incremental export:** changes since a given archive, for backups and for
  keeping two hosts in step during a move.
- **Merging:** the merge and supersession rule, if v0.4 leaves it open, and
  what happens when the same page changed in two places.
- **Alignment.** If a governed standard exists at PCP's level (an
  MCP memory or profile extension, or the profiles of the W3C AI Agent
  Memory Interoperability Community Group), PCP maps onto it and does not
  keep a parallel shape
  ([`docs/interop.md`](docs/interop.md) §11). Solid pods are in scope here
  too.

**Help wanted:** this is the least designed part of the roadmap. Use cases
are the most useful input now: who shares what with whom, and what must
never cross.

## v1.0: Stable

v1.0 is a promise that things stop moving: from then on, a breaking change
needs a new major version. It ships when these criteria are met:

1. At least three independent server implementations, from at least two
   organizations, with public conformance claims, and at least one for each
   profile.
2. At least two independent clients checked against the client profile.
3. A public interop table with round trips between at least three pairs of
   implementations.
4. An independent security review, with its findings resolved or documented.
5. One full release cycle without a breaking change.
6. At least three maintainers from at least two organizations.
7. A public decision on PCP's long-term home: an independent organization as
   today, a foundation, or a standards body.

## All along: ways to help

These do not wait for a version.

| If you... | A good first step |
|---|---|
| Build a server | Run the suite against it (`conformance/`), then open an issue with what failed and what was unclear |
| Build an AI app or agent | Connect to the reference server and tell us what a client needs that the specification does not say |
| Maintain another memory tool or format | Add or correct its mapping in [`docs/interop.md`](docs/interop.md), or write an importer |
| Know a domain (health, legal, family, finance, residency, home) | Draft the schema for its profile namespace in [`extensions/`](extensions/) |
| Work in security or privacy | Review [`SECURITY.md`](SECURITY.md) and SPEC §9, and send field reports from self-hosting |
| Run a hosting platform | Tell us what you need to offer contexts next to email and websites |
| Write or translate | Guides for implementers, and translations of the README and the guides |
| Work on standards | Help with the alignment work: MCP, W3C, Solid, data portability |

Issues labelled
[`good first issue`](https://github.com/pcp-protocol/pcp/labels/good%20first%20issue)
are small and self-contained.
[`help wanted`](https://github.com/pcp-protocol/pcp/labels/help%20wanted)
marks work nobody has picked up. To take one, say so in the issue.

## Not planned

Saying no keeps the specification small. These are out of scope unless
someone makes a strong case in an issue:

- **A new transport.** PCP stays on MCP.
- **A standard retrieval or ranking algorithm.** Retrieval is up to the
  implementation; the specification only says what it must respect
  (SPEC §5.5).
- **A second memory object model**, if a governed standard for one appears.
  PCP would map onto it.
- **A body that grants conformance.** Claims are checked against the suite,
  by anyone.
- **A service run by this project.** The project publishes a specification
  and tests, not a product.
- **Anything that needs a particular cloud, database, model or company.**

## Changing this roadmap

- **To propose an item, or to move one,** open an issue with the label
  `roadmap`. Say what problem it solves and who has it. Running code moves
  an item up.
- **To change this page,** open a pull request. Changes to the roadmap are
  editorial: they do not change what implementations must do.
- **To see what is in progress,** open [the project board](https://github.com/orgs/pcp-protocol/projects/1). It holds every issue in the milestones.
- **For questions and ideas that are not yet an issue,** use [Discussions](https://github.com/pcp-protocol/pcp/discussions).
- Maintainers review this page at every release.
- The detailed list of open questions is SPEC §11. The roadmap sorts those
  questions into versions and does not replace them.
