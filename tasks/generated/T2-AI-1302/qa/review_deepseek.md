**(a) PER-RULE**

- **R-001** CONCUR — standard customer-side prohibition on unauthorized model training; fallback clear, severity critical, realistic.
- **R-002** CONCUR — ownership/control of dedicated fine-tuned assets is a core commercial term; fallback gives ownership or exclusive use + portability; appropriate critical severity.
- **R-003** CONCUR — customer ownership of generated outputs is market; fallback includes assignment; high severity justified.
- **R-004** CONCUR — IP indemnity for model/outputs/fine-tunes is essential for customer; fallback covers all with sensible exception; critical severity proper.
- **R-005** CONCUR — anti‑competitive benchmarking restrictions should be blocked; fallback permits evaluation; high severity reasonable.
- **R-006** CONCUR — measurable uptime/latency/credits/escalation are basic procurement requirements; fallback sets minimum; high severity correct.
- **R-007** CONCUR — model change notice prevents silent swaps that break integrations; fallback 60-day notice + emergency exception; high severity appropriate.
- **R-008** CONCUR — data residency and prompt/log retention must be bounded; fallback limits to approved regions + 30 days; high severity suitable.
- **R-009** CONCUR — customer should not be bound by unilateral unbounded policy changes; fallback ties changes to law/objective safety with notice; medium severity proper.
- **R-010** CONCUR — subprocessor transparency and audit rights are standard; fallback covers list, notice, reports, and limited audit; high severity apt.
- **R-011** CONCUR — data breach and IP indemnity must be uncapped; fallback lists carve‑outs; critical severity essential.
- **R-012** CONCUR — exit must deliver fine‑tuned artifacts for portability; fallback enumerates weights/adapters/configs; high severity justified.
- **R-013** CONCUR — regulatory‑cooperation obligation is prudent for AI compliance; fallback covers documentation and cooperation; medium severity correct.
- **R-014** CONCUR — canary; Delaware law is acceptable; no issue.
- **R-015** CONCUR — canary; 99.9% uptime SLA with credits is acceptable; no issue.

**(b) PER-DEVIATION**

- **D-001 (R-002)** — VALID. The narrowing of “Customer Data” and especially “Customer Fine‑Tune Artifacts” to only config files/evaluation summaries (excluding fine‑tuned weights, adapters, embeddings) squarely contradicts R‑002’s mandate for control/ownership of dedicated model customization assets. A competent reviewer would flag it instantly. The drafting is natural for an over‑reaching vendor.
- **D-002 (R-009)** — VALID. The clause giving Vendor unfettered right to update any policy immediately on posting, “whether or not required by law or security need,” directly violates R‑009’s requirement that later changes be bound to law or objective safety with notice. Reads as a typical aggressive vendor provision; any reviewer would object.
- **D-003 (R-012)** — **QUESTIONABLE**. The exit clause omits “Customer Fine‑Tune Artifacts” but states “export … available configuration records.” Because the planted definition of Customer Fine‑Tune Artifacts is exactly configuration files and evaluation summaries, the clause effectively covers that defined set. The real problem is the definition (D-001). A human reviewer would focus on the fact that the export does not include actual model weights/adapters, but that is a consequence of D‑001, not an independent gap in Section 15. The omission of the term itself is cosmetic; the rule violation arises only from the definition. A separate deviation here is artificial and would not survive a strict review.  
  → **Verdict: QUESTIONABLE** (artificial, not a genuine independent violation).
- **D-004 (R-006)** — VALID. The gutting of SLA language to “commercially reasonable efforts” and disclaiming uptime/latency/credits/escalation as purely “aspirational” with no remedy clearly violates R‑006. The fallback requires measurable targets, credits, and escalation—all absent. Drafting is natural for a vendor trying to avoid commitments.
- **D-005 (R-001)** — VALID. The “Notwithstanding Section 4” service improvement data clause in Section 9 explicitly permits using prompts, outputs, telemetry, embeddings, and logs to “evaluate, benchmark, and improve models and services” without customer opt‑in. This directly overrides the Section 4 prohibition, which itself was already rendered toothless by the narrow definition of Customer Data. A real reviewer would see this as a clear breach of R‑001. The text is natural vendor‑favorable drafting.

**(c) DISTRACTORS & CANARIES**

- **X-001** (“This Agreement is governed by … Delaware”) — fully playbook‑compliant per R‑014; present in the document (Section 15). Valid distractor.
- **X-002** (“Vendor will provide 99.9% monthly uptime …”) — **NOT PRESENT** in the document. The agreement’s Section 8 contains only the gutted “commercially reasonable efforts” language. The listed span is a phantom; it is not a distractor from this version of the contract. The answer key is incorrect to treat it as a distractor.
- **X-003** (“Emergency changes … prompt written notice …”) — compliant with R‑007’s exception for urgent security fixes; present in Section 10. Valid distractor.
- **Canary R‑014 (Delaware law)** — deviation‑free and correctly not flagged. A reviewer might be tempted to over‑flag if they distrust Delaware, but the canary holds; no issue.
- **Canary R‑015 (99.9% uptime)** — no such clause exists in this document; there is nothing to tempt an over‑flag. The absence is irrelevant to the canary’s purpose.
- **Missing info M‑001** — genuinely absent. The agreement fails to address age‑gating, child‑directed services, or minor‑user protections, despite the client’s stated use case. Escalation is clearly warranted.

**(d) KEYWORD LEAKAGE**

Mutated spans share numerous distinctive keywords with playbook rule text, making them easily caught by a naive grep or bot:

- D‑001 definition: “prompts, prompt templates, instructions, outputs, telemetry, embeddings, fine‑tuning files, evaluation sets” — aligns heavily with R‑001, R‑002, R‑008, R‑012 lists.
- D‑005 service improvement clause: “prompts, outputs, telemetry, embeddings, and logs” — mirrors R‑001 and R‑008.
- D‑003 exit clause: “Customer Data, prompts, outputs, embeddings” — matches R‑012 and R‑001.
- D‑004 SLA wording: “uptime, latency, service credits, escalation rights” — echoes R‑006 directly.

**(e) CONTESTED ITEMS**

1. **Was D‑003 a genuine independent violation of R‑012?**  
   The exit clause says “export Customer Data, prompts, outputs, embeddings, and available configuration records.” Under the (narrow) definition, “Customer Fine‑Tune Artifacts” means configuration files and evaluation summaries, which are subsumed by “available configuration records.” Does the mere omission of the defined term “Customer Fine‑Tune Artifacts” from the exit clause, without any change to the underlying scope of what must be exported, independently violate R‑012? (Yes/No)

2. **Is distractor X‑002 valid?**  
   The answer key claims a distractor span “Vendor will provide 99.9% monthly uptime …” exists in the document. The document’s Section 8 contains only “Vendor will use commercially reasonable efforts …” and explicitly states SLAs are aspirational with no remedy. Should the non‑present text be disregarded as a distractor, and does this error affect the overall score? (Yes/No)

**(f) OVERALL**

**NEEDS REVISION FIRST.** The flagged deviations D‑001, D‑002, D‑004, and D‑005 are solid. However, D‑003 is questionable and would confuse a human red‑pen reviewer; it should be downgraded to a note or merged into D‑001. The distractor list contains a phantom entry (X‑002) not in the agreement, which must be removed. Once D‑003 is resolved and the distractor corrected, the output will be fit for human red‑pen use.