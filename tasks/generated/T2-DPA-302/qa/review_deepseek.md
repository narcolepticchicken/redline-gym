**(a) PER‑RULE**  
R‑001: **CONCUR** – binding vendor to documented instructions is foundational; fallback and critical severity are appropriate.  
R‑002: **CONCUR** – preventing internal reuse for independent business purposes is a standard controller demand; critical rightly.  
R‑003: **CONCUR** – downstream controls and pass‑through liability are essential; high severity fits.  
R‑004: **CONCUR** – concrete safeguards (encryption, access, logging, vulnerability management, incident response) are table stakes for personal data; critical is justified.  
R‑005: **CONCUR** – a fixed 48‑hour breach‑discovery clock supports regulatory response; critical aligns with GDPR‑style expectations.  
R‑006: **CONCUR** – assistance with DSARs and regulator inquiries is a necessary processor obligation; high severity is reasonable.  
R‑007: **CONCUR** – clear exit handling with return/deletion and written certification protects control; high severity.  
R‑008: **CONCUR** – practical audit rights on a reasonable cadence with cause‑based escalation are customary; medium severity is acceptable because a SOC 2‑plus‑questionnaire baseline already exists.  
R‑009: **CONCUR** – requiring a lawful transfer mechanism plus cooperation on transfer assessments is non‑negotiable; high severity.  
R‑010: **CONCUR** – personnel confidentiality duties and need‑to‑know access are basic; high severity.  
R‑011: **CONCUR** – preventing derived, telemetry and usage data from escaping the DPA avoids a major loophole; critical severity.  
R‑012: **CONCUR** – data‑protection claims must not be under‑capped or excluded; high severity.  
R‑013: **CONCUR** – DPA term should be coextensive with processing; medium severity fits.  
R‑014: **CONCUR** – (canary) the rule explicitly says an SOC 2 report is acceptable **only if** follow‑up rights remain; it is a meta‑instruction, not a rights grant.  
R‑015: **CONCUR** – (canary) a 30‑day termination assistance window is acceptable for this engagement; the rule prevents false alarm.

**(b) PER‑DEVIATION**

**D‑001 (rule R‑011, Sec. 2 Processing definition)**  
**INVALID.** The mutated span narrows the definition of “Processing” to live hosting of raw records and explicitly excludes diagnostic review, metric creation, cache retention, format conversion and support troubleshooting.  
However, R‑011 targets the **scope of “Personal Data”** – it must capture pseudonymised, aggregated, derived, telemetry and usage data. The DPA’s own definition of Personal Data already does that (“Personal Data means … information … created from Customer’s use of the services, including pseudonymized, aggregated, derived, telemetry, log, and usage data …” – Sec. 2). Therefore R‑011 is satisfied on its own terms. The narrowing of Processing is a real privacy gap, but it does not violate R‑011; it would need to be mapped to a rule about processing operations or the scope of instructions. A competent reviewer would not flag this as a breach of R‑011.

**D‑002 (rule R‑010, Sec. 6)**  
**VALID.** Replacing the obligation to bind personnel to confidentiality and provide privacy/security training with “provide internal onboarding materials” removes the core confidentiality commitment required by the rule. The omission is stark and a human reviewer would immediately recognise it as a gap.

**D‑003 (rule R‑009, Sec. 12)**  
**VALID.** The mutated text grants the vendor unfettered discretion to move hosted records among global facilities and affiliates “based on operational needs and regional capacity” without any precondition of a lawful transfer mechanism. This directly contradicts R‑009’s requirement for lawful safeguards. The text reads as a natural vendor‑friendly drafting.

**D‑004 (rule R‑008, Sec. 11)**  
**VALID.** The clause shuts down any further control review after annual assurance materials are delivered, unless the vendor agrees in writing. This eliminates the for‑cause and incident‑based audit rights that R‑008 demands, leaving the customer with no practical verification mechanism. The drafting is plausible and would be caught by a diligent review.

**D‑005 (rule R‑002, Sec. 4)**  
**VALID.** The clause explicitly permits Vendor to create commercial benchmarks, enhance offerings for other accounts, and perform other independent business uses. It swaps the protective text with an expansive reuse permission, a direct violation of R‑002. The wording is realistic and would not sound artificial to a negotiator.

**(c) DISTRACTORS, CANARIES, MISSING INFO**

**Distractors**  
X‑001 (SOC 2 report provision): Fully playbook‑compliant. It offers a report, questionnaires and other information; it does not, by itself, eliminate follow‑up rights (that is done by the separate D‑004 clause).  
X‑002 (30‑day termination assistance): Compliant and exactly the scenario R‑015 says should not be flagged.  
X‑003 (DPA precedence clause): Standard and customer‑protective; no conflict with any playbook rule.

**Canaries**  
R‑014 (SOC 2 in lieu of routine audit) and R‑015 (30‑day assistance) are both truly deviation‑free in the raw distractor text. They are temptingly easy to over‑flag because a hasty reviewer might think a SOC 2 report alone is insufficient or that a 30‑day window is too short. The actual violation in the audit space lies in D‑004, not in the distractor.

**Missing Info**

- **M‑001 “Categories of data subjects and records”** – The playbook contains no rule that explicitly requires enumerated data‑subject categories. While it is good practice to list them in a schedule, the absence does not breach any stated rule and is not clearly escalation‑worthy within the four corners of this playbook–document pair. The client context (records normalisation for a mid‑size tech company) does not elevate it to an automatic escalation; I dissent from the drafter’s default to escalate.  
- **M‑002 “Current subprocessor list location”** – Although the DPA mentions a notice‑and‑objection process, it provides no URL, portal reference or schedule identifying the current subprocessors. Without that, the customer cannot practically exercise its approval/objection rights under R‑003. This is genuinely absent and escalation‑worthy.

**(d) KEYWORD LEAKAGE**

Only **D‑005** contains a distinctive keyword shared with the playbook. The mutated text allows the vendor to “create commercial **benchmarks**”, while R‑002’s position and fallback use “benchmarking”. A simple grep or keyword‑based bot would immediately surface this span as a candidate. No other deviation’s mutated span shares distinctive terms with its corresponding rule text.

**(e) CONTESTED ITEMS**

1. **Does the narrowed definition of “Processing” in Section 2 (D‑001) violate Rule R‑011?**  
   Drafter answer (implicit in mapping): Yes. My answer: No — R‑011 governs the definition of Personal Data, which already includes derived, telemetry and usage data; the Processing definition reduction is a separate concern.

2. **Should the absence of explicit categories of data subjects (M‑001) be escalated?**  
   Drafter: Escalate. My answer: No — the playbook does not contain a matching requirement, and the context does not make it an obvious escalation; it exceeds the playbook’s scope.

**(f) OVERALL**  
**NEEDS REVISION.** D‑001 is mis‑attributed to R‑011 and should be either re‑mapped to a rule that addresses the scope of processing obligations (or removed from the deviation list if it cannot be linked to a playbook rule). M‑001 escalation is aggressive without a clear playbook anchor; either provide a stronger justification tied to a rule (e.g., transparency principles) or drop it. The remaining deviations (D‑002, D‑003, D‑004, D‑005), distractors, and missing M‑002 are well‑formed and usable.