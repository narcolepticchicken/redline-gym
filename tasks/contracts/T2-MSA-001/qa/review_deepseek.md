(a) PER-RULE  
- R-001: CONCUR. Annual-spend cap with carve-outs for high-risk categories (privacy, secrecy, defense, infringement, gross misconduct) is standard in reasonably negotiated tech-procurement agreements.  
- R-002: CONCUR. Mutual defense obligations that cover IP infringement and law violations balance risk appropriately; it’s the norm in a commercial services deal.  
- R-003: CONCUR. Client ownership of project-specific work product plus a perpetual license to pre-existing embedded materials is a defensible position; it avoids hostage risk.  
- R-004: CONCUR. 72-hour reporting matches regulatory timing needs (GDPR, state breach laws); the position is commercially sound despite being tight.  
- R-005: CONCUR. Written instructions, safeguards, and legal compliance are foundational for processing personal data; no company would accept less.  
- R-006: CONCUR. Optional 30-day exit with no penalty beyond accrued fees preserves flexibility; it’s a reasonable buyer term.  
- R-007: CONCUR. Customer-controlled renewal of ≤1 year prevents auto-lock-in; a sensible stance for services with evolving needs.  
- R-008: CONCUR. Carving express warranties, indemnities, and remedies out of a general disclaimer is standard to avoid illusory promises.  
- R-009: CONCUR. Bilateral written amendment prevents unilateral changes; it’s a baseline control.  
- R-010: CONCUR. Consent required, with a merger/reorganization exception mirroring industry practice.  
- R-011: CONCUR. $5M E&O/cyber and $2M GL is typical for a production data-processing engagement; a reasonable ask.  
- R-012: CONCUR. Audit rights (annual, with cause-based increase) are commercially normal for privacy/security assurance.  
- R-013: CONCUR. Written downstream commitments at equivalent protection are essential when subcontractors touch sensitive data.  
- R-014: CONCUR. Accepting net-45 payment terms as a canary is appropriate; it’s not a deviation from this playbook.  
- R-015: CONCUR. Delaware governing law is a benign canary; no reason to escalate.

(b) PER-DEVIATION  
- D-001 (R-001) – **VALID**. The Section 18 sentence “Despite any contrary sentence, all recovery for Section 13 or Section 14 claims is limited to the amount stated in Section 16.” directly undercuts the liability carve-outs in Section 16, capping confidentiality and indemnity claims. A competent reviewer would instantly spot the conflict. The text is blunt but reads like an aggressive vendor override—not unnatural.  
- D-002 (R-006) – **VALID**. Section 12’s exit charge “equal to the full unpaid balance for that Order Form” imposes a penalty far beyond accrued, undisputed fees, nullifying the convenience termination right in Section 11. The language “exit charge” is a touch odd but still plausible in a hostile termination-for-convenience clause.  
- D-003 (R-003) – **VALID**. The definition of “Deliverables” in Section 2 explicitly “excludes Vendor Methods created, refined, or reduced to practice during the engagement,” then Section 8 assigns only Deliverables, giving only a license to embedded Vendor Methods. This carves out bespoke methods that would otherwise be client-owned work product. It’s a real-world tactic and would be flagged.  
- D-004 (R-004) – **QUESTIONABLE**. The narrowed definition of “Security Incident” in Section 2 (confirmed outbound extraction plus forensic report) is planted as a violation, but the agreement’s notification clause (Section 6) never uses that term; it relies on the undefined phrase “Covered Event.” Consequently, this definitional mutation does not actually alter the reporting obligation, so a human reviewer would see no direct impact on R-004 compliance. The mutation feels like a planted trap that doesn’t connect.  
- D-005 (R-013) – **VALID**. Section 7 omits any requirement to bind subcontractors to written commitments as protective as Vendor’s own. The text “Vendor remains responsible for their work as if performed by Vendor” is a common insufficiency, so it reads naturally.  
- D-006 (R-004) – **VALID**. Section 6 replaces the 72-hour period with “thirty business days after its incident lead confirms a Covered Event.” Even though “Covered Event” is undefined, the timeline is a direct, detectable violation of the 72‑hour rule. The undefined term adds obfuscation but doesn’t mask the timing failure.  
- D-007 (R-007) – **VALID**. Section 10 imposes automatic three-year renewals with a 180‑day non-continuation window. This is a textbook lock-in that erases customer control; the drafting is standard auto-renewal language and would be caught.

(c) DISTRACTORS & CANARIES  
- X-001 (net‑45 payment): Fully compliant with playbook canary R‑014. The clause “undisputed invoices are due forty-five days after Customer receives the invoice” is exactly the term the playbook accepts, making it a genuine honeypot that could tempt false escalation.  
- X-002 (Delaware governing law): Compliant with canary R‑015. The clause “This Agreement is governed by the laws of the State of Delaware” is unobtrusive and a true negative test.  
- X-003 (1% monthly interest on late payments): Not addressed by any playbook rule; the provision “Vendor may charge interest on undisputed overdue amounts at one percent per month or the highest rate allowed by law, whichever is lower” is aggressive but entirely outside the playbook’s scope. It will not cause a false positive.  
- MISSING-INFO: M‑001 (processing geography/cross-border transfer basis) and M‑002 (certified deletion at exit) are genuinely absent. The MSA contains no mention of hosting region, data residency, transfer impact assessment, or any deletion certificate. Given the client context of processing customer personal data, both are clearly escalation-worthy.

(d) KEYWORD LEAKAGE  
No mutated span shares distinctive keywords or phrases with the playbook rule texts or fallback language that a simple grep bot would reliably trigger. Highlights:  
- D-001: “limited to the amount stated in Section 16” – none of the carve-out terms from R‑001 fallback appear.  
- D-002: “full unpaid balance” – absent from R‑006 fallback.  
- D-003: “Vendor Methods” – not in R‑003.  
- D-004: “confirmed outbound extraction … forensic report” – no match with “unauthorized access, acquisition, use, loss, or disclosure.”  
- D-005: no distinctive keywords.  
- D-006: “thirty business days” – no overlap with “72 hours.”  
- D-007: “three years” – playbook specifies “no more than one year.”  
Thus the instance passes an anti-keyword-leak check.

(e) CONTESTED ITEMS  
1. Does the mutation D‑004 (narrowing “Security Incident” in Section 2) constitute a valid, machine-scorable deviation from R‑004, given that the notification clause (Section 6) does not cross-reference that definition and instead uses the undefined term “Covered Event”?  
2. Does D‑003’s exclusion of “Vendor Methods created, refined, or reduced to practice during the engagement” from the Deliverables definition unambiguously violate R‑003’s requirement that bespoke work product prepared for the client belong to the client, or could a reasonable interpreter find it a permissible retention of pre-existing/general methods?  
3. Is the D‑001 override sentence in Section 18 (“Despite any contrary sentence, all recovery for Section 13 or Section 14 claims is limited to the amount stated in Section 16”) so blunt that it reads as planted rather than as a realistic, albeit aggressive, vendor drafting error?

(f) OVERALL  
**NEEDS REVISION FIRST**. The instance contains a well-constructed set of deviations, distractors, and missing-info items, but D‑004 is structurally flawed: the narrowed definition has no operational effect because the notification clause relies on an undefined term rather than “Security Incident.” This ambiguity would confuse a human red-pen review and undermines machine scorability. To be fit for human review, either delete D‑004 or revise Section 6 to refer explicitly to the narrowed “Security Incident” definition (e.g., change “Covered Event” to “Security Incident”), thereby making the mutation’s impact unambiguous.