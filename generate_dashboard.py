#!/usr/bin/env python3
"""Render reviewable static dashboard artifacts from one normalized snapshot."""

from __future__ import annotations

import argparse
import html
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


VALID_STATES = {"ok", "stale", "failed"}


def parse_iso8601(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def validate_snapshot(snapshot: dict[str, Any]) -> None:
    if not isinstance(snapshot.get("title"), str) or not snapshot["title"].strip():
        raise ValueError("snapshot.title must be a non-empty string")
    sources = snapshot.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ValueError("snapshot.sources must be a non-empty list")
    for source in sources:
        if not isinstance(source.get("name"), str) or not source["name"].strip():
            raise ValueError("each source needs a non-empty name")
        if source.get("state") not in VALID_STATES:
            raise ValueError(f"invalid source state: {source.get('state')!r}")
        if source["state"] == "failed" and not source.get("error"):
            raise ValueError("failed sources need an error")
        if source.get("observed_at"):
            parse_iso8601(source["observed_at"])


def render_markdown(snapshot: dict[str, Any], generated_at: str) -> str:
    lines = [
        f"# {snapshot['title']}",
        "",
        f"Generated: `{generated_at}`",
        "",
        "| Source | State | Observed at | Notes |",
        "| --- | --- | --- | --- |",
    ]
    for source in snapshot["sources"]:
        notes = source.get("error") or ", ".join(
            f"{key}={value}" for key, value in source.get("metrics", {}).items()
        ) or "No metrics reported"
        lines.append(
            "| {name} | {state} | {observed} | {notes} |".format(
                name=source["name"],
                state=source["state"],
                observed=source.get("observed_at") or "not available",
                notes=notes,
            )
        )
    lines.extend([
        "",
        "## Interpretation boundary",
        "",
        "A successful renderer means only that this snapshot was transformed into "
        "artifacts. It does not make a stale or failed source current. Review the "
        "source-state column before using any metric.",
        "",
    ])
    return "\n".join(lines)


def render_html(snapshot: dict[str, Any], generated_at: str) -> str:
    rows = []
    for source in snapshot["sources"]:
        notes = source.get("error") or ", ".join(
            f"{key}={value}" for key, value in source.get("metrics", {}).items()
        ) or "No metrics reported"
        rows.append(
            "<tr><td>{}</td><td><span class=\"state {}\">{}</span></td>"
            "<td>{}</td><td>{}</td></tr>".format(
                html.escape(source["name"]),
                html.escape(source["state"]),
                html.escape(source["state"]),
                html.escape(source.get("observed_at") or "not available"),
                html.escape(notes),
            )
        )
    warning = any(source["state"] != "ok" for source in snapshot["sources"])
    notice = (
        "<p class=\"notice\">One or more sources are stale or failed. "
        "This page is not a fully current view.</p>"
        if warning
        else "<p class=\"notice ok\">All sources report an OK state.</p>"
    )
    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>{html.escape(snapshot['title'])}</title>
  <style>
    :root {{ color-scheme: light; --ink: #17212b; --muted: #556371; --line: #d6dde3; --warn: #8a4b00; --bad: #9b1b30; --ok: #167241; }}
    body {{ margin: 0; background: #f7f9fb; color: var(--ink); font: 16px/1.5 system-ui, sans-serif; }}
    main {{ max-width: 920px; margin: 0 auto; padding: 40px 20px 64px; }}
    h1 {{ margin: 0; font-size: 30px; }} .muted {{ color: var(--muted); }}
    .notice {{ margin: 24px 0; padding: 12px 14px; border-left: 4px solid var(--warn); background: #fff8eb; color: #5a3500; }}
    .notice.ok {{ border-color: var(--ok); background: #edf8f1; color: #125a32; }}
    table {{ width: 100%; border-collapse: collapse; background: #fff; border: 1px solid var(--line); }}
    th, td {{ padding: 12px; text-align: left; vertical-align: top; border-bottom: 1px solid var(--line); }}
    th {{ color: var(--muted); font-size: 13px; }} tr:last-child td {{ border-bottom: 0; }}
    .state {{ font-weight: 700; text-transform: uppercase; font-size: 12px; }}
    .state.ok {{ color: var(--ok); }} .state.stale {{ color: var(--warn); }} .state.failed {{ color: var(--bad); }}
  </style>
</head>
<body><main>
  <h1>{html.escape(snapshot['title'])}</h1>
  <p class=\"muted\">Generated {html.escape(generated_at)}</p>
  {notice}
  <table><thead><tr><th>Source</th><th>State</th><th>Observed at</th><th>Notes</th></tr></thead>
  <tbody>{''.join(rows)}</tbody></table>
  <p class=\"muted\">A successful build verifies this transformation, not the freshness of a stale or failed upstream source.</p>
</main></body></html>
"""


def generate(input_path: Path, output_dir: Path, generated_at: str) -> None:
    snapshot = json.loads(input_path.read_text(encoding="utf-8"))
    validate_snapshot(snapshot)
    parse_iso8601(generated_at)
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {"generated_at": generated_at, **snapshot}
    (output_dir / "dashboard.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "status.md").write_text(render_markdown(snapshot, generated_at), encoding="utf-8")
    (output_dir / "index.html").write_text(render_html(snapshot, generated_at), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--generated-at",
        default=datetime.now(UTC).replace(microsecond=0).isoformat(),
        help="ISO-8601 timestamp used in all generated outputs",
    )
    args = parser.parse_args()
    generate(args.input, args.output, args.generated_at)


if __name__ == "__main__":
    main()
