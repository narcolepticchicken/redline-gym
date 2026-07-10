#!/usr/bin/env python3
"""Build the T2-N counter-family guided attorney red-pen sitting page.

Reads all 32 counter families across generator/t2n_families/*.json and
renders one review card per family, cross-referencing playbook rule text
(position/fallback/escalation_trigger) from the actual playbooks/ files
(not from a copy embedded in the family JSON) so drift would be caught.

Usage: python3 scripts/make_family_sitting_page.py OUT.html
"""
from __future__ import annotations

import html
import json
import pathlib
import re
import sys
from typing import Any

GYM = pathlib.Path(__file__).resolve().parents[1]
E = html.escape

# Filename stem (generator/t2n_families/<AREA>.json) -> attorney-facing label.
AREA_LABELS = {
    "ai": "AI",
    "contracts": "Contracts",
    "crypto": "Crypto",
    "employment": "Employment",
    "governance": "Governance",
    "ma": "M&A",
    "privacy": "Privacy",
}
AREAS = ["ai", "contracts", "crypto", "employment", "governance", "ma", "privacy"]

RULED_BORDERLINE_ID = "CF-MSA-LIABILITY-V2"
RULED_BORDERLINE_TEXT = "RULED: ceiling only 2026-07-10"


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def slug(text: str) -> str:
    keep = []
    for ch in text.lower():
        if ch.isalnum():
            keep.append(ch)
        elif keep and keep[-1] != "-":
            keep.append("-")
    return "".join(keep).strip("-")


def fam_box(cid: str, label: str) -> str:
    """Checkbox with a stable data-k id AND a data-label so the clipboard
    export can name unchecked boxes without re-parsing DOM text."""
    return (
        f'<label class="ok"><input type="checkbox" data-k="{E(cid)}" '
        f'data-label="{E(label)}"> {E(label)}</label>'
    )


# ---------------------------------------------------------------------------
# Predicate -> plain-English translation (deterministic, no LLM, no network).
# ---------------------------------------------------------------------------

_TOKEN_RE = re.compile(
    r"""
    '[^']*'                     |  # string literal
    ==|!=|>=|<=|>|<             |  # comparisons
    [(){},]                     |  # punctuation
    [A-Za-z_][A-Za-z0-9_]*      |  # identifier / keyword
    \d+                            # number
    """,
    re.VERBOSE,
)

_OP_WORDS = {
    "==": "equals",
    "!=": "does not equal",
    ">=": "is at least",
    "<=": "is at most",
    ">": "is more than",
    "<": "is less than",
}
_KEYWORDS = {"and": "AND", "or": "OR", "not": "NOT"}


def _spacify(ident: str) -> str:
    return ident.replace("_", " ")


def translate_predicate(expr: str) -> str:
    """Deterministic string-transform: python-ish boolean expression ->
    readable prose. Unrecognized tokens pass through unchanged rather than
    crashing (this is read-only supporting context, not the primary
    artifact)."""
    try:
        toks = _TOKEN_RE.findall(expr)
        out: list[str] = []
        i = 0
        n = len(toks)
        while i < n:
            t = toks[i]
            if t == "in" and i + 1 < n and toks[i + 1] == "{":
                j = i + 2
                items = []
                while j < n and toks[j] != "}":
                    if toks[j] == ",":
                        j += 1
                        continue
                    items.append(_spacify(toks[j].strip("'")))
                    j += 1
                out.append("is one of: " + ", ".join(items))
                i = j + 1
                continue
            if t in _OP_WORDS:
                out.append(_OP_WORDS[t])
            elif t in _KEYWORDS:
                out.append(_KEYWORDS[t])
            elif t in ("(", ")", "{", "}", ","):
                out.append(t)
            elif t.startswith("'") and t.endswith("'"):
                out.append(_spacify(t.strip("'")))
            elif re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", t):
                out.append(_spacify(t))
            else:
                out.append(t)  # defensive passthrough
            i += 1
        text = " ".join(out)
        text = text.replace("( ", "(").replace(" )", ")")
        text = re.sub(r"\s+", " ", text).strip()
        return text or expr
    except Exception:
        # Defensive: never let a translation quirk crash page generation.
        return expr


# ---------------------------------------------------------------------------
# Playbook rule lookup (source of truth is playbooks/, not the family JSON's
# own embedded copy of position/fallback/escalation_trigger).
# ---------------------------------------------------------------------------

_playbook_cache: dict[pathlib.Path, dict[str, Any]] = {}


def load_playbook_rule(area: str, playbook_id: str, rule_id: str) -> dict[str, str]:
    path = GYM / "playbooks" / area / f"{playbook_id}.json"
    if path not in _playbook_cache:
        if not path.exists():
            raise SystemExit(f"playbook file not found: {path}")
        _playbook_cache[path] = read_json(path)
    pb = _playbook_cache[path]
    for rule in pb.get("rules", []):
        if rule.get("rule_id") == rule_id:
            return {
                "position": rule.get("position", ""),
                "fallback": rule.get("fallback", ""),
                "escalation_trigger": rule.get("escalation_trigger", ""),
            }
    raise SystemExit(f"rule_id {rule_id} not found in {path}")


def slots_line(render: dict[str, Any], decoy_ids: list[str]) -> str:
    parts = []
    for key, val in render.get("counter_text_slots", {}).items():
        parts.append(f"{key}: {val}")
    for key, val in render.get("phase1_context_slots", {}).items():
        parts.append(f"{key}: {val}")
    decoy_values = render.get("decoy_values", [])
    if decoy_values:
        if len(decoy_values) == len(decoy_ids):
            for did, dval in zip(decoy_ids, decoy_values):
                parts.append(f"{did}: {dval}")
        else:
            # Length mismatch: list values without labels rather than crash.
            parts.append("decoy values: " + ", ".join(str(v) for v in decoy_values))
    return " | ".join(parts) if parts else "(no slot values)"


def render_box(kind: str, render: dict[str, Any], decoy_ids: list[str]) -> str:
    label = "Acceptable" if kind == "acceptable" else "Unacceptable"
    text = E(render.get("text", ""))
    slots = E(slots_line(render, decoy_ids))
    return f"""<div class="render-box {kind}">
      <div class="render-label">{label}</div>
      <p class="render-text">{text}</p>
      <p class="render-slots">{slots}</p>
    </div>"""


def render_family_card(area: str, playbook_id: str, fam: dict[str, Any]) -> tuple[str, int, int]:
    cfid = fam["counter_family_id"]
    rule_id = fam["rule_id"]
    fam_slug = slug(cfid)
    area_label = AREA_LABELS.get(area, area.title())

    grounding = load_playbook_rule(area, playbook_id, rule_id)
    predicate = fam.get("predicate", {})
    expr = predicate.get("expression", "")
    english = translate_predicate(expr)

    decoy_ids = fam.get("decoy_ids", [])
    pools = fam.get("render_pools", {})
    acceptable = pools.get("acceptable", [])
    unacceptable = pools.get("unacceptable", [])

    render_count = 0
    render_boxes = []
    for r in acceptable:
        render_boxes.append(render_box("acceptable", r, decoy_ids))
        render_count += 1
    for r in unacceptable:
        render_boxes.append(render_box("unacceptable", r, decoy_ids))
        render_count += 1

    ruled_banner = ""
    if cfid == RULED_BORDERLINE_ID:
        ruled_banner = f'<div class="ruled-banner">{E(RULED_BORDERLINE_TEXT)}</div>'

    checks = "".join(
        [
            fam_box(f"{fam_slug}-boundary", "Boundary correct"),
            fam_box(f"{fam_slug}-realistic", "Renders realistic"),
            fam_box(f"{fam_slug}-conflict", "No cross-rule conflict"),
        ]
    )
    check_count = 3

    card = f"""<div class="family-card" id="{E(fam_slug)}" data-fam-id="{E(cfid)}" data-rule-id="{E(rule_id)}">
  <div class="fam-head">
    <span class="badge">{E(area_label)}</span>
    <span class="badge">{E(playbook_id)}</span>
    <span class="badge">{E(rule_id)}</span>
    <h2>{E(cfid)}</h2>
  </div>
  {ruled_banner}
  <div class="grounding">
    <p><b>Position:</b> <span class="verbatim">{E(grounding["position"])}</span></p>
    <p><b>Fallback:</b> <span class="verbatim">{E(grounding["fallback"])}</span></p>
    <p><b>Escalation trigger:</b> <span class="verbatim">{E(grounding["escalation_trigger"])}</span></p>
  </div>
  <div class="predicate">
    <p class="predicate-en"><b>Plain English:</b> {E(english)}</p>
    <p class="predicate-label"><b>Raw expression:</b></p>
    <code>{E(expr)}</code>
  </div>
  <div class="render-grid">
    {''.join(render_boxes)}
  </div>
  <div class="fam-checks">
    {checks}
  </div>
  <textarea data-note-text="{E(fam_slug)}-note" placeholder="Objections / notes..."></textarea>
</div>"""

    return card, render_count, check_count


def build_page(out_path: pathlib.Path) -> tuple[str, int, int, int]:
    cards: list[str] = []
    total_families = 0
    total_renders = 0
    total_checks = 0

    for area in AREAS:
        data = read_json(GYM / "generator" / "t2n_families" / f"{area}.json")
        playbook_ids = sorted(k for k in data.keys() if k != "_status")
        for playbook_id in playbook_ids:
            fams = data[playbook_id]["counter_families"]
            for fam in fams:
                card, render_count, check_count = render_family_card(area, playbook_id, fam)
                cards.append(card)
                total_families += 1
                total_renders += render_count
                total_checks += check_count

    # Sanity comment only, never used as a hardcoded total below:
    # 32 families * 3 checkboxes/family = 96 expected checks.

    page = f"""<!doctype html><html><head><meta charset="utf-8">
<title>T2-N counter family sitting v1</title>
<style>
 :root {{
   --bg: #fafaf7; --fg: #1a1a1a; --dim: #666; --card-bg: #fff; --card-border: #e2e2dc;
   --accent: #1c4f9c; --code-bg: #f2f2ee; --acc-bg: #f0f7f0; --acc-border: #4a9b52;
   --unacc-bg: #fdf3f3; --unacc-border: #c0392b; --ruled-bg: #fff6e0; --ruled-border: #b8860b;
   --bar-bg: #1a1a1a; --bar-fg: #fff; --fill: #7cc47f; --meter-bg: #444;
 }}
 @media (prefers-color-scheme: dark) {{
   :root {{
     --bg: #16161a; --fg: #e8e8e4; --dim: #9a9a95; --card-bg: #1f1f24; --card-border: #33333a;
     --accent: #6f9ceb; --code-bg: #2a2a30; --acc-bg: #16281a; --acc-border: #4a9b52;
     --unacc-bg: #2c1616; --unacc-border: #e06456; --ruled-bg: #2e2708; --ruled-border: #d9a441;
     --bar-bg: #0c0c0e; --bar-fg: #fff; --fill: #7cc47f; --meter-bg: #3a3a3a;
   }}
 }}
 body {{ font-family: -apple-system, sans-serif; margin: 0; color: var(--fg); background: var(--bg); }}
 main {{ max-width: 900px; margin: 0 auto; padding: 24px 20px 140px; }}
 h1 {{ font-size: 1.4rem; }} h2 {{ font-size: 1.1rem; margin: 0; }}
 .dim {{ color: var(--dim); font-size: .92rem; }}
 .lead {{ background: var(--card-bg); border: 1px solid var(--card-border); border-left: 4px solid var(--accent); border-radius: 8px; padding: 14px 18px; }}
 .family-card {{ background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 10px; padding: 18px 20px; margin: 22px 0; scroll-margin-top: 20px; }}
 .fam-head {{ display: flex; align-items: center; flex-wrap: wrap; gap: 8px; margin-bottom: 10px; }}
 .badge {{ display: inline-block; font-size: .74rem; color: var(--dim); border: 1px solid var(--card-border); border-radius: 999px; padding: 2px 9px; }}
 .ruled-banner {{ background: var(--ruled-bg); border: 1px solid var(--ruled-border); border-left: 5px solid var(--ruled-border); border-radius: 6px; padding: 8px 14px; font-weight: 700; margin: 8px 0 14px; }}
 .grounding p {{ margin: 6px 0; white-space: pre-wrap; }}
 .verbatim {{ font-weight: 400; }}
 .predicate {{ background: var(--code-bg); border-radius: 8px; padding: 10px 14px; margin: 12px 0; }}
 .predicate-en {{ margin: 4px 0; }}
 .predicate-label {{ margin: 8px 0 2px; }}
 .predicate code {{ display: block; white-space: pre-wrap; word-break: break-word; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: .86rem; background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 6px; padding: 8px 10px; }}
 .render-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 10px; margin: 14px 0; }}
 .render-box {{ border-radius: 8px; padding: 10px 12px; border-left-width: 5px; border-left-style: solid; border-top: 1px solid var(--card-border); border-right: 1px solid var(--card-border); border-bottom: 1px solid var(--card-border); }}
 .render-box.acceptable {{ background: var(--acc-bg); border-left-color: var(--acc-border); }}
 .render-box.unacceptable {{ background: var(--unacc-bg); border-left-color: var(--unacc-border); }}
 .render-label {{ font-weight: 700; font-size: .78rem; text-transform: uppercase; letter-spacing: .03em; margin-bottom: 4px; }}
 .render-box.acceptable .render-label {{ color: var(--acc-border); }}
 .render-box.unacceptable .render-label {{ color: var(--unacc-border); }}
 .render-text {{ margin: 4px 0; line-height: 1.45; }}
 .render-slots {{ margin: 6px 0 0; font-size: .8rem; color: var(--dim); font-family: ui-monospace, SFMono-Regular, Menlo, monospace; word-break: break-word; }}
 .fam-checks {{ display: flex; flex-wrap: wrap; gap: 6px 18px; margin-top: 14px; }}
 .ok {{ display: inline-flex; align-items: center; font-weight: 600; color: var(--accent); }}
 .ok input {{ transform: scale(1.2); margin-right: 6px; }}
 textarea {{ width: 100%; min-height: 70px; box-sizing: border-box; border: 1px solid var(--card-border); border-radius: 8px; padding: 10px 12px; font: inherit; margin-top: 10px; background: var(--card-bg); color: var(--fg); }}
 button {{ font: inherit; cursor: pointer; }}
 #copy-notes-btn {{ background: var(--accent); color: #fff; border: none; border-radius: 6px; padding: 8px 14px; font-weight: 600; }}
 #bar {{ position: fixed; bottom: 0; left: 0; right: 0; background: var(--bar-bg); color: var(--bar-fg); padding: 12px 20px; font-size: .95rem; }}
 #meter {{ height: 8px; background: var(--meter-bg); border-radius: 999px; margin-top: 8px; overflow: hidden; }}
 #fill {{ height: 100%; width: 0%; background: var(--fill); }}
</style></head><body><main>

<h1>T2-N counter family sitting v1</h1>
<div class="lead">
 <p>Guided attorney red-pen review of all {total_families} T2-N counter families. For each family: confirm the
 boundary is correct, the eight renders (4 acceptable / 4 unacceptable) read as realistic contract text, and
 there is no conflict with other rules.</p>
 <p class="dim">All checks and notes persist in localStorage key <b>family-sitting-v1</b>.</p>
 <p><button id="copy-notes-btn" type="button">Copy notes to clipboard</button></p>
</div>

{''.join(cards)}

</main>
<div id="bar"><span id="count"></span><div id="meter"><div id="fill"></div></div></div>
<script>
 const KEY = 'family-sitting-v1';
 const boxes = [...document.querySelectorAll('input[type="checkbox"][data-k]')];
 const textareas = [...document.querySelectorAll('textarea[data-note-text]')];
 const state = JSON.parse(localStorage.getItem(KEY) || '{{"checks":{{}},"notes":{{}}}}');
 state.checks = state.checks || {{}};
 state.notes = state.notes || {{}};
 boxes.forEach(b => {{
   b.checked = !!state.checks[b.dataset.k];
   b.addEventListener('change', () => {{
     state.checks[b.dataset.k] = b.checked;
     save();
     update();
   }});
 }});
 textareas.forEach(t => {{
   t.value = state.notes[t.dataset.noteText] || '';
   t.addEventListener('input', () => {{
     state.notes[t.dataset.noteText] = t.value;
     save();
   }});
 }});
 function save() {{ localStorage.setItem(KEY, JSON.stringify(state)); }}
 function update() {{
   const k = boxes.filter(b => b.checked).length;
   const pct = boxes.length ? (100 * k / boxes.length) : 0;
   document.getElementById('fill').style.width = pct.toFixed(1) + '%';
   document.getElementById('count').textContent = k + ' / ' + boxes.length +
     (k === boxes.length ? ' - all confirmed.' : ' confirmed');
 }}
 update();

 function buildNotesMarkdown() {{
   const lines = ['# Family sitting notes', ''];
   let any = false;
   document.querySelectorAll('.family-card').forEach(card => {{
     const famId = card.dataset.famId || '';
     const ruleId = card.dataset.ruleId || '';
     const cardBoxes = [...card.querySelectorAll('input[type="checkbox"][data-k]')];
     const unchecked = cardBoxes.filter(b => !b.checked).map(b => b.dataset.label || b.dataset.k);
     const ta = card.querySelector('textarea[data-note-text]');
     const note = ta ? ta.value.trim() : '';
     const allChecked = unchecked.length === 0;
     if (allChecked && !note) return;
     any = true;
     lines.push('## ' + famId + ' (' + ruleId + ')');
     if (unchecked.length) {{
       lines.push('- Unchecked: ' + unchecked.join(', '));
     }} else {{
       lines.push('- Checkboxes: all checked');
     }}
     if (note) {{
       lines.push('- Note: ' + note);
     }}
     lines.push('');
   }});
   if (!any) {{ lines.push('_All families fully confirmed with no notes._'); }}
   return lines.join('\\n');
 }}

 function copyNotesFallback(md) {{
   const ta = document.createElement('textarea');
   ta.value = md;
   ta.style.position = 'fixed';
   ta.style.top = '0';
   ta.style.left = '0';
   ta.style.opacity = '0';
   document.body.appendChild(ta);
   ta.focus();
   ta.select();
   let ok = false;
   try {{ ok = document.execCommand('copy'); }} catch (e) {{ ok = false; }}
   document.body.removeChild(ta);
   if (ok) {{
     alert('Notes copied to clipboard (fallback method).');
   }} else {{
     window.prompt('Clipboard blocked - copy manually (select all, then Ctrl/Cmd+C):', md);
   }}
 }}

 document.getElementById('copy-notes-btn').addEventListener('click', () => {{
   const md = buildNotesMarkdown();
   if (navigator.clipboard && navigator.clipboard.writeText) {{
     navigator.clipboard.writeText(md).then(() => {{
       alert('Notes copied to clipboard.');
     }}).catch(() => copyNotesFallback(md));
   }} else {{
     copyNotesFallback(md);
   }}
 }});
</script></body></html>"""
    out_path.write_text(page)
    return str(out_path), total_families, total_renders, total_checks


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python3 scripts/make_family_sitting_page.py OUT.html", file=sys.stderr)
        return 2
    out_path = pathlib.Path(argv[1])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    written, families, renders, checks = build_page(out_path)
    print(f"wrote: {written}")
    print(f"total_families: {families}")
    print(f"total_renders: {renders}")
    print(f"total_checkboxes: {checks}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
