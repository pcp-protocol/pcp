"""The report a conformance claim links to: JSON for tools, Markdown to read.

One entry per requirement id, so a claim can say "AUTH-25 pass, SEC-10 fail"
and a reader can check it. The legacy `findings` list is kept as it was.
"""
import datetime

from . import __version__

SPEC_VERSION = "0.3"
FORMAT = 1
ORDER = ("fail", "warn", "pass", "skip", "manual")
SECRET_OPTIONS = ("token", "second_token", "delegated_token")


def _rollup(statuses):
    for s in ORDER:
        if s in statuses:
            return s
    return "manual"


def _skip_kind(fs):
    """One id skipped for two reasons counts as not run: that is the one a claim must settle."""
    kinds = {f.skip_kind for f in fs if f.status == "skip"}
    return "not_run" if "not_run" in kinds else "not_applicable"


def build(reqs, findings, opts, doc, doc_url, profile, duration, notices=()):
    by_id = {}
    for f in findings:
        by_id.setdefault(f.id, []).append(f)
    entries = []
    for rid, r in reqs.items():
        fs = by_id.get(rid, [])
        entry = {
            "id": rid, "level": r.level, "section": r.section, "profile": r.profile,
            "check": r.check,
            "status": _rollup({f.status for f in fs}),
            "messages": [(f"{f.status}: {f.message}" if len(fs) > 1 else f.message) for f in fs if f.message],
        }
        if entry["status"] == "skip":
            entry["skip_kind"] = _skip_kind(fs)
        entries.append(entry)
    summary = {s: sum(1 for e in entries if e["status"] == s) for s in ORDER}
    skipped = {k: sum(1 for e in entries if e.get("skip_kind") == k) for k in ("not_run", "not_applicable")}
    used = {k: v for k, v in vars(opts).items()
            if k not in SECRET_OPTIONS + ("endpoint", "timeout") and v not in (None, False)
            and not (k == "revocation_wait" and v == 300)}
    for k in SECRET_OPTIONS:
        if getattr(opts, k, None):
            used[k] = "(given)"
    return {
        "report_format": FORMAT,
        "suite": {"name": "pcp-conformance", "version": __version__},
        "spec_version": SPEC_VERSION,
        "profile": profile,
        "date": datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "endpoint": opts.endpoint,
        "context_document": doc_url,
        "claims": (doc or {}).get("conformance"),
        "options": used,
        "duration_s": duration,
        "requirement_summary": summary,
        "skipped": skipped,
        "notices": list(notices),
        "requirements": entries,
    }


def markdown(rep):
    s = rep["requirement_summary"]
    out = [f"# PCP conformance report",
           "",
           f"- Suite: {rep['suite']['name']} {rep['suite']['version']}",
           f"- PCP version: {rep['spec_version']}",
           f"- Profile: {rep['profile']}",
           f"- Run: {rep['date']}",
           f"- Endpoint: {rep['endpoint']}",
           f"- Options: {' '.join('--' + k.replace('_', '-') for k in rep['options']) or 'none (read-only run)'}",
           "",
           "| Pass | Fail | Warn | Skipped | Manual or review |",
           "|---:|---:|---:|---:|---:|",
           f"| {s['pass']} | {s['fail']} | {s['warn']} | {s['skip']} | {s['manual']} |",
           ""]
    k = rep.get("skipped") or {}
    if s["skip"]:
        out += [f"Of the skipped: {k.get('not_run', 0)} not run, {k.get('not_applicable', 0)} not applicable.", ""]
    for n in rep.get("notices") or []:
        out += [f"**Note.** {n}", ""]
    titles = {"fail": ("Failed (MUST)", None), "warn": ("Warnings (SHOULD not met)", None),
              "not_run": ("Skipped: not run (not a pass; run it or have a person check it, see SPEC 10.3)", "skip"),
              "not_applicable": ("Skipped: not applicable (the context does not use the feature)", "skip")}
    for key, (title, status) in titles.items():
        rows = [e for e in rep["requirements"]
                if e["status"] == (status or key) and (status is None or e.get("skip_kind") == key)]
        if not rows:
            continue
        out += [f"## {title}", ""]
        for e in rows:
            msg = "; ".join(e["messages"])
            out.append(f"- `{e['id']}` ({e['level']}, SPEC {e['section']}): {msg}".rstrip(": "))
        out.append("")
    for st, title in (("pass", "Passed"), ("manual", "Manual or review: checked by a person")):
        ids = [e["id"] for e in rep["requirements"] if e["status"] == st]
        if ids:
            out += [f"## {title} ({len(ids)})", "", ", ".join(f"`{i}`" for i in ids), ""]
    return "\n".join(out)
