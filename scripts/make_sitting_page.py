#!/usr/bin/env python3
"""Build Aaron's consolidated release-sitting review page.

Usage: python3 scripts/make_sitting_page.py OUT.html
"""
from __future__ import annotations

import html
import json
import pathlib
import sys
from collections import defaultdict
from typing import Any


GYM = pathlib.Path(__file__).resolve().parents[1]
E = html.escape

TASKS_HAND_BUILT = [
    "tasks/contracts/T1-NDA-001",
    "tasks/contracts/T2-MSA-001",
]
TASKS_SAMPLED = [
    "tasks/generated/T2-DPA-302",
    "tasks/generated/T2-EMP-702",
    "tasks/generated/T2-AI-1302",
]

MECH = {
    "direct_term_swap": "a term was swapped outright",
    "cross_ref_override": "a later clause quietly overrides an earlier compliant one",
    "defined_term_shift": "a definition was poisoned so a compliant-looking clause does nothing",
    "omission": "something required was quietly left out",
    "off_playbook_addition": "an off-playbook clause was added",
    "cross_doc_override": "another document overrides this one",
}
ACTION = {
    "redline_with_fallback": "Fix the wording (redline)",
    "escalate": "Don't edit - raise it with the client",
    "flag_only": "Flag it; no edit needed",
}


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def box(cid: str, label: str) -> str:
    return f'<label class="ok"><input type="checkbox" data-k="{E(cid)}"> {E(label)}</label>'


def slug(text: str) -> str:
    keep = []
    for ch in text.lower():
        if ch.isalnum():
            keep.append(ch)
        elif keep and keep[-1] != "-":
            keep.append("-")
    return "".join(keep).strip("-")


def format_list(values: list[str]) -> str:
    return ", ".join(f'"{E(str(v))}"' for v in values)


def render_markdown_doc(text: str) -> str:
    paras = []
    for block in text.split("\n\n"):
        b = block.strip()
        if not b:
            continue
        if b.startswith("### "):
            paras.append(f"<h4>{b[4:]}</h4>")
        elif b.startswith("## "):
            paras.append(f"<h3>{b[3:]}</h3>")
        elif b.startswith("# "):
            paras.append(f"<h2>{b[2:]}</h2>")
        else:
            paras.append(f"<p>{b}</p>")
    return "\n".join(paras)


def highlighted_contract(task_dir: pathlib.Path, devs: list[dict[str, Any]]) -> tuple[str, list[str]]:
    docs = sorted((task_dir / "docs").glob("*.md"))
    failures: list[str] = []
    contract_parts: list[str] = []

    for docp in docs:
        body = E(docp.read_text())
        for d in devs:
            span = E(d["mutated_text"])
            count = body.count(span)
            if count == 1:
                body = body.replace(
                    span,
                    f'<mark id="mk-{E(d["deviation_id"])}">'
                    f'<span class="tag">mistake {E(d["deviation_id"][-1])}</span>{span}</mark>',
                    1,
                )
        if len(docs) > 1:
            contract_parts.append(f"<h3 class='docname'>{E(docp.name)}</h3>")
        contract_parts.append(render_markdown_doc(body))

    contract_html = "\n".join(contract_parts)
    for d in devs:
        if f'id="mk-{E(d["deviation_id"])}"' not in contract_html:
            failures.append(d["deviation_id"])
    return contract_html, failures


def render_instance(task_rel: str, prefix: str) -> tuple[str, int, list[str]]:
    task_dir = GYM / task_rel
    task = read_json(task_dir / "task.json")
    planted = read_json(task_dir / "planted_deviations.json")
    playbook = read_json(GYM / task["playbook_ref"])
    rules = {r["rule_id"]: r for r in playbook["rules"]}
    devs = planted["deviations"]
    violated_ids = {d["rule_id"] for d in devs}
    canaries = [r for r in playbook["rules"] if r.get("is_canary")]
    plain_rules = [
        r
        for r in playbook["rules"]
        if not r.get("is_canary") and r["rule_id"] not in violated_ids
    ]
    contract_html, span_failures = highlighted_contract(task_dir, devs)
    key = f"{prefix}-{task['task_id']}"

    mistake_cards = []
    for i, d in enumerate(devs, 1):
        r = rules[d["rule_id"]]
        fallback = ""
        if d["expected_action"] == "redline_with_fallback":
            fallback = f" - rewrite it as: <i>{E(r['fallback'])}</i>"
        mistake_cards.append(
            f"""<div class="card">
      <h3>Mistake {i} of {len(devs)} <span class="dim">({E(MECH.get(d["mechanism"], d["mechanism"]))})</span></h3>
      <p><b>Your rulebook says:</b> {E(r["position"])}</p>
      <p class="now"><b>But this contract says</b> (section {E(str(d["clause_anchor"]["section"]))}):<br>{E(d["mutated_text"])}</p>
      <p class="fix"><b>The response the AI must give:</b> {E(ACTION[d["expected_action"]])}{fallback}</p>
      {box(key + "-d-" + d["deviation_id"], "Yes - real mistake, right response")}
    </div>"""
        )

    rules_cards = []
    for r in plain_rules:
        rules_cards.append(
            f"""<div class="card slim">
      <p><b>{E(r["rule_id"])}.</b> {E(r["position"])}</p>
      {box(key + "-r-" + r["rule_id"], "Yes - a real company would want this")}
    </div>"""
        )

    traps = []
    for r in canaries:
        traps.append(
            f"""<div class="card slim">
      <p><b>Trap ({E(r["rule_id"])}):</b> {E(r["position"])}</p>
      {box(key + "-r-" + r["rule_id"], "Yes - the contract is fine here")}
    </div>"""
        )
    for x in planted.get("distractors", []):
        xid = x.get("distractor_id", x.get("id", "X"))
        traps.append(
            f"""<div class="card slim">
      <p><b>Unusual but fine ({E(xid)}):</b> {E(x.get("span", x.get("text", "")))}</p>
      <p class="dim">{E(x.get("why_benign", ""))}</p>
      {box(key + "-x-" + xid, "Yes - no edit deserved")}
    </div>"""
        )
    for m in planted.get("missing_info", []):
        mid = m.get("missing_info_id", m.get("id", "M"))
        desc = m.get("description", m.get("topic", ""))
        traps.append(
            f"""<div class="card slim">
      <p><b>Missing on purpose ({E(mid)}):</b> {E(desc)}</p>
      {box(key + "-m-" + mid, "Yes - a good lawyer would raise this")}
    </div>"""
        )

    count = len(devs) + len(plain_rules) + len(canaries) + len(planted.get("distractors", [])) + len(planted.get("missing_info", [])) + 1
    html_block = f"""
<section id="{E(slug(task["task_id"]))}">
<h2>{E(task["task_id"])} - compact red-pen walkthrough</h2>
<div class="lead">
 <p>A fake contract with <b>{len(devs)} deliberate mistakes</b>, plus a rulebook saying what a good contract looks like for this client.</p>
 <p><b>Confirm three things:</b> each planted mistake is real with the right fix; the rulebook positions are ones a real company would take; the contract reads like a real contract.</p>
 <p class="dim">Scenario: {E(task["client_context"])}</p>
</div>

<h3>Part 1 - The {len(devs)} planted mistakes</h3>
{''.join(mistake_cards)}

<h3>Part 2 - The rest of the rulebook ({len(plain_rules)} rules the contract already follows)</h3>
{''.join(rules_cards)}

<h3>Part 3 - Traps and deliberate gaps</h3>
<p class="dim">The traps are clauses that are perfectly fine - an AI that "finds a problem" there is guessing. The gaps are things missing on purpose that a good lawyer should raise.</p>
{''.join(traps)}

<h3>Part 4 - Read it once as a lawyer</h3>
<p class="dim">Yellow marks are the planted mistakes (the AI won't see them highlighted). Does the rest read like a normal contract, and do the marked clauses sound like real drafting?</p>
<div class="contract">{contract_html}</div>
<div class="card">{box(key + "-readthrough", "Yes - reads like a real contract, nothing sounds fake")}</div>
</section>
"""
    return html_block, count, span_failures


def load_missing_item(playbook_id: str, expected_topic_part: str) -> tuple[dict[str, Any], str]:
    sources = [
        GYM / "generator" / "recipes" / f"{playbook_id}.json",
        GYM / "generator" / "bases" / f"{playbook_id}.json",
    ]
    for path in sources:
        if not path.exists():
            continue
        data = read_json(path)
        for item in data.get("missing_info", []):
            topic = item.get("topic", "").lower()
            anchor = item.get("context_anchor", "").lower()
            haystack = topic + " " + anchor + " " + " ".join(item.get("match_keywords", []))
            if expected_topic_part.lower() in haystack:
                return item, str(path.relative_to(GYM))
    raise SystemExit(f"missing_info record not found for {playbook_id}: {expected_topic_part}")


def render_rulings() -> tuple[str, int]:
    dpa_item, dpa_source = load_missing_item("PB-DPA-001", "records of processing")
    emp_item, emp_source = load_missing_item("PB-EMP-001", "280g")

    q3 = """<div class="card">
      <h3>Q3 V4-threshold ruling</h3>
      <p>An independent expert reader finds <b>4 of 7 planted mistakes</b> on the hand-built MSA.</p>
      <p>Pick the release rule Aaron wants to apply:</p>
      <label class="ok choice"><input type="radio" name="q3-ruling" data-note="q3_ruling" value="keep-60"> Keep 60 percent threshold - this instance fails and gets reworked.</label>
      <label class="ok choice"><input type="radio" name="q3-ruling" data-note="q3_ruling" value="lower-t2-55"> Lower the T2 threshold to 55 percent - 4/7 passes.</label>
      <label class="ok choice"><input type="radio" name="q3-ruling" data-note="q3_ruling" value="accept-with-note"> Accept this per-instance with a note.</label>
    </div>"""
    q2 = f"""<div class="card">
      <h3>Q2 confirmation - fix at source</h3>
      <p>The policy is already applied: confirmed answer-key omissions and below-floor base text are repaired in bases/templates; answer keys stay exhaustive.</p>
      {box("rulings-q2-fix-at-source", "Confirm fix-at-source policy")}
    </div>"""

    def swap_item(prefix: str, title: str, item: dict[str, Any], source: str) -> str:
        return f"""<div class="subcard">
      <p><b>{E(title)}</b></p>
      <p><b>Source:</b> {E(source)}</p>
      <p><b>Context anchor:</b> "{E(item["context_anchor"])}"</p>
      <p><b>Match keywords:</b> {format_list(item["match_keywords"])}</p>
      {box(prefix, "Confirm this missing-info answer-key authorship item")}
    </div>"""

    swaps = f"""<div class="card">
      <h3>Two flagged answer-key authorship swaps</h3>
      {swap_item(
          "rulings-dpa-records-processing-swap",
          "DPA records-of-processing missing-info item",
          dpa_item,
          dpa_source,
      )}
      {swap_item(
          "rulings-emp-280g-swap",
          "EMP 280G missing-info item",
          emp_item,
          emp_source,
      )}
    </div>"""

    cards = [
        q3,
        q2,
        swaps,
    ]
    return "<h2>Rulings</h2>\n" + "\n".join(cards), 3


def render_playbooks() -> tuple[str, int]:
    by_area: dict[str, list[pathlib.Path]] = defaultdict(list)
    for path in sorted((GYM / "playbooks").glob("*/*.json")):
        by_area[path.parent.name].append(path)

    sections = ["<h2>Playbooks</h2>"]
    count = 0
    for area in sorted(by_area):
        sections.append(f'<section id="playbook-{E(slug(area))}"><h3>{E(area.title())}</h3>')
        for path in by_area[area]:
            pb = read_json(path)
            sections.append(
                f'<div class="lead"><p><b>{E(pb["playbook_id"])}</b> - {E(pb.get("title", path.stem))}</p>'
                '<p class="dim">Confirm each client position below. Use the same plain-English test as the red-pen pages: would a real company want this in the rulebook?</p></div>'
            )
            for rule in pb["rules"]:
                badge = "canary" if rule.get("is_canary") else "rule"
                cid = f"playbook-{pb['playbook_id']}-{rule['rule_id']}"
                sections.append(
                    f"""<div class="card slim">
      <p><b>{E(rule["rule_id"])}</b> <span class="badge {badge}">{E(badge)}</span> <span class="badge">{E(rule.get("severity", "unknown"))}</span></p>
      <p><b>Position:</b> {E(rule["position"])}</p>
      <p><b>Fallback:</b> {E(rule["fallback"])}</p>
      {box(cid, "Yes - a real company would want this")}
    </div>"""
                )
                count += 1
        sections.append("</section>")
    return "\n".join(sections), count


def build_page(out_path: pathlib.Path) -> tuple[str, int, dict[str, list[str]]]:
    ruling_html, ruling_count = render_rulings()
    playbooks_html, playbooks_count = render_playbooks()

    hand_html = ["<h2>Hand-Built Instances</h2>"]
    sampled_html = ["<h2>Sampled Generated Instances</h2>"]
    total = ruling_count + playbooks_count
    span_failures: dict[str, list[str]] = {}

    for rel in TASKS_HAND_BUILT:
        block, count, failures = render_instance(rel, "hand")
        hand_html.append(block)
        total += count
        if failures:
            span_failures[pathlib.Path(rel).name] = failures

    for rel in TASKS_SAMPLED:
        block, count, failures = render_instance(rel, "sample")
        sampled_html.append(block)
        total += count
        if failures:
            span_failures[pathlib.Path(rel).name] = failures

    page = f"""<!doctype html><html><head><meta charset="utf-8">
<title>Aaron release sitting v01</title>
<style>
 body {{ font-family: -apple-system, sans-serif; margin: 0; color: #1a1a1a; background: #fafaf7; }}
 main {{ max-width: 780px; margin: 0 auto; padding: 24px 20px 130px; }}
 h1 {{ font-size: 1.4rem; }} h2 {{ margin-top: 2.4em; font-size: 1.15rem; }} h3 {{ margin: 1.2em 0 .5em; font-size: 1.02rem; }}
 .dim {{ color: #666; font-size: .92rem; }} .docname {{ color: #666; border-bottom: 1px solid #ddd; }}
 .lead {{ background: #fff; border: 1px solid #e2e2dc; border-left: 4px solid #1c4f9c; border-radius: 8px; padding: 14px 18px; }}
 .card {{ background: #fff; border: 1px solid #e2e2dc; border-radius: 8px; padding: 16px 18px; margin: 12px 0; }}
 .card.slim {{ padding: 10px 16px; }}
 .subcard {{ border-top: 1px solid #ecece7; margin-top: 12px; padding-top: 12px; }}
 .now {{ background: #fdf3f3; padding: 10px 12px; border-radius: 6px; }}
 .fix {{ background: #f0f7f0; padding: 10px 12px; border-radius: 6px; }}
 .ok {{ display: block; margin-top: 10px; font-weight: 600; color: #1c4f9c; }}
 .ok input {{ transform: scale(1.25); margin-right: 8px; }}
 .choice {{ color: #1a1a1a; font-weight: 500; }}
 .badge {{ display: inline-block; font-family: -apple-system, sans-serif; font-size: .72rem; color: #555; border: 1px solid #ddd; border-radius: 999px; padding: 1px 7px; margin-left: 5px; }}
 .badge.canary {{ color: #8a5a00; border-color: #e6c36a; background: #fff8df; }}
 .contract {{ background: #fff; border: 1px solid #e2e2dc; border-radius: 8px; padding: 26px 32px; font-family: Georgia, serif; line-height: 1.55; }}
 mark {{ background: #fff3bf; border-bottom: 2px solid #e6a700; scroll-margin-top: 20px; }}
 mark .tag {{ font-family: -apple-system, sans-serif; font-size: .68rem; background: #e6a700; color: #fff; border-radius: 8px; padding: 1px 6px; margin-right: 5px; }}
 textarea {{ width: 100%; min-height: 90px; box-sizing: border-box; border: 1px solid #d6d6d0; border-radius: 8px; padding: 10px 12px; font: inherit; }}
 #bar {{ position: fixed; bottom: 0; left: 0; right: 0; background: #1a1a1a; color: #fff; padding: 12px 20px; font-size: .95rem; }}
 #meter {{ height: 8px; background: #444; border-radius: 999px; margin-top: 8px; overflow: hidden; }}
 #fill {{ height: 100%; width: 0%; background: #7cc47f; }}
</style></head><body><main>

<h1>Aaron release sitting v01</h1>
<div class="lead">
 <p>This is the single human-review sitting page for the current release decision. Confirm the rulings, playbook rules, hand-built instances, and sampled generated instances.</p>
 <p class="dim">All checks persist in localStorage key <b>sitting-v01</b>.</p>
</div>

{ruling_html}
{playbooks_html}
{''.join(hand_html)}
{''.join(sampled_html)}

<h2>Done</h2>
<div class="lead">
 <p>When complete tell your assistant <b>"sitting done"</b> plus any items flagged.</p>
 <p class="dim">Use this box for anything Aaron wants the assistant to know after the sitting.</p>
 <textarea data-note-text="flagged_items" placeholder="Items flagged..."></textarea>
</div>
</main>
<div id="bar"><span id="count"></span><div id="meter"><div id="fill"></div></div></div>
<script>
 const KEY = 'sitting-v01';
 const boxes = [...document.querySelectorAll('input[type="checkbox"][data-k]')];
 const radios = [...document.querySelectorAll('input[type="radio"][data-note]')];
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
 radios.forEach(r => {{
   r.checked = state.notes[r.dataset.note] === r.value;
   r.addEventListener('change', () => {{
     if (r.checked) {{
       state.notes[r.dataset.note] = r.value;
       save();
     }}
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
     (k === boxes.length ? ' - all confirmed. Say "sitting done" plus any items flagged.' : ' confirmed');
 }}
 update();
</script></body></html>"""
    out_path.write_text(page)
    return str(out_path), total, span_failures


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python3 scripts/make_sitting_page.py OUT.html", file=sys.stderr)
        return 2
    out_path = pathlib.Path(argv[1])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    written, total, failures = build_page(out_path)
    print(f"wrote: {written}")
    print(f"total_checkboxes: {total}")
    if failures:
        print(f"span_highlight_failures: {len(failures)}")
        for task_id, dev_ids in failures.items():
            print(f"{task_id}: {', '.join(dev_ids)}")
    else:
        print("span_highlight_failures: 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
