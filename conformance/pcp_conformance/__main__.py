"""Command line: run checks against a server, check archives, self-check.

  python3 -m pcp_conformance run --endpoint URL [options]
  python3 -m pcp_conformance archive FILE [--keys keys.json]
  python3 -m pcp_conformance roundtrip A B [--cross]
  python3 -m pcp_conformance self-check
"""
import argparse
import json
import sys
import time
import traceback

import os

from . import __version__, archive, report as reportmod
from .registry import CHECKS, Recorder, Skip, load_requirements, self_check
from .target import Options, Target
from .checks import discovery, oauth_flow, tools, memory, team, optional  # noqa: F401 (registers checks)

COLORS = {"pass": "32", "fail": "31", "warn": "33", "skip": "90", "manual": "36"}


def _paint(status, text, color):
    return f"\033[{COLORS[status]}m{text}\033[0m" if color else text


def run(args):
    reqs = load_requirements()
    opts = Options(**{k: v for k, v in vars(args).items() if k not in ("cmd", "func")})
    t = Target(opts, out=lambda s: print(s, file=sys.stderr))
    color = sys.stdout.isatty() and not args.json
    findings, crashed = [], []
    only = set(args.only.split(",")) if args.only else None
    started = time.time()
    for fn in CHECKS:
        if only and not (only & set(fn.ids)) and fn.__name__ not in only:
            continue
        rec = Recorder(reqs, fn.__name__)
        try:
            if fn.writes and not opts.allow_writes:
                raise Skip("writes test data; run with --allow-writes against a throwaway context")
            fn(t, rec)
        except Skip as e:
            done = {f.id for f in rec.findings}
            for rid in fn.ids:
                if rid not in done:
                    rec.skip(rid, str(e))
        except Exception as e:
            crashed.append(fn.__name__)
            done = {f.id for f in rec.findings}
            for rid in fn.ids:
                if rid not in done:
                    rec.fail(rid, f"check {fn.__name__} crashed: {type(e).__name__}: {e}")
            if args.verbose:
                traceback.print_exc()
        findings += rec.findings
    # One line per id and status; a skip is dropped when another check settled the id.
    settled = {f.id for f in findings if f.status != "skip"}
    seen, kept = set(), []
    for f in findings:
        key = (f.id, f.status, f.message, f.skip_kind)
        if (f.status == "skip" and f.id in settled) or key in seen:
            continue
        seen.add(key)
        kept.append(f)
    findings = kept
    covered = {f.id for f in findings}
    for rid, r in reqs.items():
        if rid not in covered and not r.suite:
            findings.append(_manual(r))
    profile = args.profile or _profile_of(t)
    _apply_profile(findings, reqs, profile)
    summary = {s: sum(1 for f in findings if f.status == s) for s in Recorder.STATUSES}
    not_run = sum(1 for f in findings if f.skip_kind == "not_run")
    notices = _notices(t, profile)
    report = {
        "suite": f"pcp-conformance {__version__}",
        "endpoint": opts.endpoint,
        "context_document": t._cache.get("doc_url"),
        "claims": (t._cache.get("doc") or {}).get("conformance"),
        "duration_s": round(time.time() - started, 1),
        "summary": summary,
        "notices": notices,
        "findings": [dict(f.as_dict(), level=reqs[f.id].level, section=reqs[f.id].section) for f in findings],
    }
    if args.json:
        json.dump(report, sys.stdout, indent=2)
        print()
    else:
        order = {s: i for i, s in enumerate(("fail", "warn", "pass", "skip", "manual"))}
        for f in sorted(findings, key=lambda f: (order[f.status], f.id)):
            if f.status == "manual" and not args.verbose:
                continue
            label = "N/A" if f.skip_kind == "not_applicable" else f.status.upper()
            line = f"{label:6} {f.id:9} {reqs[f.id].level:6} §{reqs[f.id].section:10} {f.message}"
            print(_paint(f.status, line, color))
        print(f"\n{summary['pass']} pass, {summary['fail']} fail, {summary['warn']} warn, "
              f"{summary['skip']} skip, {summary['manual']} manual or review (use -v to list)")
        if summary["skip"]:
            print(f"skipped: {summary['skip'] - not_run} not applicable (N/A), {not_run} not run (SKIP). "
                  "The ones not run still count: SPEC §10.3")
        for n in notices:
            print(_paint("warn", f"NOTE   {n}", color))
    if args.report or args.report_md or args.report_dir:
        full = reportmod.build(reqs, findings, opts, (t._cache.get("doc") or {}), t._cache.get("doc_url"),
                               profile, report["duration_s"], notices)
        full["findings"] = report["findings"]  # the list `run` has always written
        paths = {}
        if args.report_dir:
            os.makedirs(args.report_dir, exist_ok=True)
            paths["json"] = os.path.join(args.report_dir, "pcp-report.json")
            paths["md"] = os.path.join(args.report_dir, "pcp-report.md")
        paths["json"] = args.report or paths.get("json")
        paths["md"] = args.report_md or paths.get("md")
        if paths["json"]:
            with open(paths["json"], "w") as fh:
                json.dump(full, fh, indent=2)
                fh.write("\n")
        if paths["md"]:
            with open(paths["md"], "w") as fh:
                fh.write(reportmod.markdown(full) + "\n")
        for kind in ("json", "md"):
            if paths[kind]:
                print(f"report written: {paths[kind]}", file=sys.stderr)
    return 1 if summary["fail"] else 0


def _profile_of(t):
    """The profile the run is for, when the server's own claim names exactly one."""
    claim = (t._cache.get("doc") or {}).get("conformance")
    profiles = claim.get("profiles") if isinstance(claim, dict) else claim
    if isinstance(profiles, list) and len(profiles) == 1:
        return str(profiles[0])
    return "unspecified"


PROFILE_ONLY = {"personal": "P", "team": "T"}


def _apply_profile(findings, reqs, profile):
    """SPEC 10.3: a run is for one profile. A requirement of the other profile
    only, which no check settled, does not apply to this run."""
    if profile not in PROFILE_ONLY:
        return
    other = next(v for k, v in PROFILE_ONLY.items() if k != profile)
    name = {"P": "Personal", "T": "Team"}[other]
    for f in findings:
        if reqs[f.id].profile.strip() == other and f.status in ("skip", "manual"):
            f.status, f.skip_kind = "skip", "not_applicable"
            f.message = f"belongs to the {name} profile only; this run is for the {profile} profile"


def _notices(t, profile="unspecified"):
    """Things a reader of the report must know that no single requirement says."""
    doc = t._cache.get("doc")
    if profile not in PROFILE_ONLY:
        return ["This run names no profile, so every requirement was treated as possibly applying. "
                "A claim is for one profile (SPEC §10.3): pass --profile personal or --profile team."] + _notices(t, "personal")
    if isinstance(doc, dict) and doc.get("export") is not True:
        return ["No conformance claim is possible from this run: discovery `export` is not `true` "
                "(SPEC §10.3 item 4), so the export checks did not run."]
    return []


def _manual(r):
    from .registry import Finding
    how = {"M": "check by hand on the management surface or consent screen",
           "R": "needs review evidence (documentation, code review)",
           "A": "checked on an export archive: python3 -m pcp_conformance archive FILE"}[r.check]
    return Finding(r.id, "manual", how)


def cmd_archive(args):
    keys = json.load(open(args.keys))["keys"] if args.keys else {}
    problems, manifest = archive.check(args.file, keys)
    for p in problems:
        print(f"FAIL {p}")
    if not problems:
        print(f"ok   {args.file}: {len((manifest or {}).get('files', []))} files, hashes and counts check")
    return 1 if problems else 0


def cmd_roundtrip(args):
    problems = archive.roundtrip(args.a, args.b, same_implementation=not args.cross)
    for p in problems:
        print(f"FAIL {p}")
    if not problems:
        print("ok   round trip holds (" + ("across implementations" if args.cross else "same implementation") + ")")
    return 1 if problems else 0


def cmd_self_check(args):
    reqs = load_requirements()
    problems = self_check(reqs)
    for p in problems:
        print(f"FAIL {p}")
    n = sum(1 for r in reqs.values() if r.suite)
    print(f"{len(reqs)} requirements, {n} for the suite, {len(CHECKS)} checks; "
          f"{'coverage complete' if not problems else str(len(problems)) + ' problems'}")
    return 1 if problems else 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="pcp-conformance", description="PCP v0.3 conformance suite")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="run the checks against a server")
    r.add_argument("--endpoint", help="the context's MCP endpoint URL")
    r.add_argument("--discovery", help="the context document URL, if the endpoint alone does not find it")
    r.add_argument("--other-endpoint", help="MCP endpoint of a second context of the same person (AUTH-25, CTX-06)")
    r.add_argument("--token", help="an access token to use instead of running OAuth")
    r.add_argument("--token-scopes", help="the scopes of --token, space separated (default: the default grant)")
    r.add_argument("--client-id", help="a pre-registered or CIMD client id")
    r.add_argument("--interactive", action="store_true", help="approve authorizations in a browser")
    r.add_argument("--allow-writes", action="store_true", help="write test pages under pcp-conformance/<run>/")
    r.add_argument("--allow-load", action="store_true", help="send request bursts (rate-limit check)")
    r.add_argument("--allow-register", action="store_true", help="register OAuth clients and probe the CIMD fetcher")
    r.add_argument("--revocation-wait", type=int, default=300, help="seconds to wait for revocation (AUTH-28)")
    r.add_argument("--scan-path", help="the server's data directory, searched for the custody canary (KEY-05)")
    r.add_argument("--second-token", help="a token of a second principal (team checks)")
    r.add_argument("--second-login", help="login_hint for a second principal on a test-mode server")
    r.add_argument("--private-partition", help="a partition the first principal writes and the second cannot read")
    r.add_argument("--delegated-token", help="an agent token acting for a human (delegation checks)")
    r.add_argument("--only", help="comma-separated requirement ids or check names")
    r.add_argument("--insecure", action="store_true", help="do not verify TLS certificates")
    r.add_argument("--timeout", type=int, default=15)
    r.add_argument("--json", action="store_true", help="print the report as JSON")
    r.add_argument("--profile", choices=tuple(PROFILE_ONLY), help="the profile this run is for (personal or team), recorded in the report")
    r.add_argument("--report", help="also write the JSON report to this file")
    r.add_argument("--report-md", help="also write a readable Markdown report to this file")
    r.add_argument("--report-dir", help="write pcp-report.json and pcp-report.md into this directory")
    r.add_argument("-v", "--verbose", action="store_true")
    r.set_defaults(func=run)
    a = sub.add_parser("archive", help="check an export archive (SPEC §8.3)")
    a.add_argument("file")
    a.add_argument("--keys", help="JSON file with {\"keys\": {kid: hex}} for file-level JWE")
    a.set_defaults(func=cmd_archive)
    rt = sub.add_parser("roundtrip", help="compare an archive with the one exported after restoring it (SPEC §8.8)")
    rt.add_argument("a")
    rt.add_argument("b")
    rt.add_argument("--cross", action="store_true", help="the two archives come from different implementations")
    rt.set_defaults(func=cmd_roundtrip)
    s = sub.add_parser("self-check", help="every suite requirement and standard tool has a check")
    s.set_defaults(func=cmd_self_check)
    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
