# Answer-Key Defects

## tasks/contracts/T2-MSA-001

- V3_clean_base R-005 section 5: The section allows Vendor to process Customer Data for purposes beyond the Customer's documented instructions—specifically, 'to provide and support the services' and 'as otherwise expressly authorized in an Order Form'—which is less restrictive than the fallback's requirement to process Customer Data only under documented instructions.
  Quote: Vendor will process Customer Data only to provide and support the services, to comply with Customer's documented instructions, and as otherwise expressly authorized in an Order Form.
- V3_clean_base R-006 section 11: The section requires payment of 'approved reimbursable expenses' but does not require them to be undisputed or approved in writing, potentially allowing charges beyond accrued, undisputed amounts, violating the rule's prohibition on penalties beyond undisputed amounts.
  Quote: Customer will pay fees for services performed before the effective termination date and approved reimbursable expenses incurred before that date.
- V3_clean_base R-007 section 10: The section omits the fallback's cap of 'no more than one year' for the initial term, allowing an Order Form to specify a longer initial term without the signed approval required by the rule for commitments exceeding one year.
  Quote: Each Order Form has the initial term stated in it and will not automatically extend unless Customer signs a renewal order or gives written approval for a renewal period of one year or less.
- V4_round_trip_extra R-002 section 14: The section limits Vendor's defense obligation to IP infringement and law violations, omitting coverage for third-party claims arising from Vendor's breach of contract or other materials it provides, which the fallback requires. This makes the provision less protective than the minimum standard.
  Quote: Customer will defend and indemnify Vendor against third-party claims arising from Customer materials, Customer's unlawful use of the services, or use of the services contrary to this Agreement.
- V4_round_trip_extra R-004 section 2,6: The definition of 'Security Incident' limits the trigger to confirmed outbound extraction of Customer Data evidenced by a completed forensic report approved by Vendor's incident response lead. This is narrower than the fallback's requirement to notify Customer of any suspected or actual unauthorized access to, acquisition of, use of, loss of, or disclosure of Customer Data, and would delay or prevent notification required by the rule, making it non-compliant.
  Quote: "Security Incident" means confirmed outbound extraction of Customer Data that is evidenced by a completed written forensic report approved by Vendor's incident response lead. Vendor will give written alert within thirty business days after its incident lead confirms a Security Incident.

## tasks/generated/T1-DPA-301

- V3_clean_base R-005 section 8. Breach Notice: The section requires notice within 72 hours, which is less protective than the fallback's 48-hour limit. A 72-hour timeline may prevent the controller from meeting its own 72-hour regulatory notification deadline, undermining the rule's goal of supporting controller obligations.
  Quote: Vendor will notify Customer without undue delay and in any event within 72 hours after discovering a Personal Data Breach.
- V4_round_trip_extra R-011 section 2: The section narrows the definition of Personal Data by including pseudonymised, aggregated, derived, telemetry, log, and usage data only 'to the extent such data relates to a person, household, device, customer account, or customer dataset.' The fallback requires all such data created from or relating to Customer personal data to be treated as personal data unless irreversibly anonymised. The section's qualification creates a gap where data derived from customer personal data but not directly tied to an individual, household, device, account, or dataset could be excluded, contravening the rule's objective to close de-identification loopholes.
  Quote: 'Personal Data' means information relating to an identified or identifiable person that is provided by or for Customer, processed on behalf of Customer, or created from Customer's use of the services, including pseudonymized, aggregated, derived, telemetry, log, and usage data to the extent such data relates to a person, household, device, customer account, or customer dataset.

## tasks/generated/T1-MSA-105

- V3_clean_base R-002 section 14: The section omits Vendor's obligation to defend and indemnify Customer for claims arising from Vendor's breach or materials, making it less protective than the fallback which requires each party to cover claims from the indemnifying party's breach, unlawful conduct, or materials it provides.
  Quote: Vendor will defend and indemnify Customer against third-party claims alleging that the services or Deliverables infringe intellectual property rights or that Vendor's performance violates applicable law.
- V3_clean_base R-007 section 10: The section allows an initial term longer than one year without Customer's signed approval, as it omits the fallback's requirement that each Order Form have an initial term of no more than one year.
  Quote: Each Order Form has the initial term stated in it and will not automatically extend unless Customer signs a renewal order or gives written approval for a renewal period of one year or less.
- V4_round_trip_extra R-002 section 14: The section omits the fallback's mutual requirement that each party indemnify the other for claims arising from any breach of the agreement. Vendor's indemnity is limited to IP infringement and law violations, not all breaches or claims relating to materials Vendor provides. Customer's indemnity only covers unlawful use and use contrary to the agreement, not all breaches or unlawful conduct generally. The section is less protective than the fallback.
  Quote: Vendor will defend and indemnify Customer against third-party claims alleging that the services or Deliverables infringe intellectual property rights or that Vendor's performance violates applicable law. Customer will defend and indemnify Vendor against third-party claims arising from Customer materials, Customer's unlawful use of the services, or use of the services contrary to this Agreement.
- V4_round_trip_extra R-006 section 11: The section does not limit reimbursable expenses to those that are undisputed, as required by the fallback and the rule's position that only accrued, undisputed amounts may be charged. This omission could result in the customer owing disputed amounts, making the language less protective.
  Quote: Customer will pay fees for services performed before the effective termination date and approved reimbursable expenses incurred before that date.

## tasks/generated/T1-NDA-101

- V4_round_trip_extra R-007 section 5: The section omits the fallback's explicit timing requirement that notice and cooperation occur 'Before any compelled disclosure,' making it less protective because notice could be provided after disclosure.
  Quote: If Recipient is required by law, regulation, subpoena, court order, or governmental request to disclose Confidential Information, Recipient will, to the extent legally permitted, provide prompt notice to Discloser and reasonably cooperate with Discloser in seeking confidential or protective treatment.

## tasks/generated/T1-NDA-103

- V3_clean_base R-012 section 12: The section contains a residual knowledge clause that is not shown to have been expressly approved by the client, directly violating the rule that such clauses be absent unless approved. The fallback would delete the clause entirely unless approved in writing, so the section's presence is less protective than the fallback.
  Quote: No right to use residual knowledge, unaided memory, or retained impressions is granted under this Agreement unless the parties approve that right in a signed writing.
- V4_round_trip_extra R-004 section 3: The section text does not define or limit 'the Purpose' to the activities listed in the fallback (evaluate, negotiate, and if agreed perform), so it is ambiguous and could permit broader use, making it less protective.
  Quote: Recipient may use Confidential Information solely for the Purpose. 'Purpose' means evaluating, negotiating, and, if agreed, performing the contemplated analytics modernization between the parties.
- V4_round_trip_extra R-012 section 12: The section contains an explicit residual knowledge clause. The rule requires such clauses to be absent unless expressly approved by the client, and no such approval is indicated.
  Quote: No right to use residual knowledge, unaided memory, or retained impressions is granted under this Agreement unless the parties approve that right in a signed writing.

## tasks/generated/T2-DPA-303

- V4_round_trip_extra R-001 section 5: The section permits processing to 'improve the services' without requiring documented instructions, which is less restrictive than the fallback's requirement to process only on documented instructions.
  Quote: Vendor will process Personal Data only to provide, secure, support, and improve the services for Customer
- V4_round_trip_extra R-007 section 11: The section allows retention for 'archival controls' in addition to legally required copies, exceeding the fallback's exception and failing to fully restore customer control.
  Quote: Retained copies required by law or archival controls remain subject to this DPA until deleted.

## tasks/generated/T2-MSA-104

- V3_clean_base R-007 section 10: The section allows the initial term to be stated in the Order Form without any cap, and does not require Customer's signed approval if that initial term exceeds one year. The fallback explicitly limits the initial term to no more than one year. The provided text is less protective, enabling lock-in beyond one year without Customer's explicit approval, violating the rule.
  Quote: Each Order Form has the initial term stated in it and will not automatically extend unless Customer signs a renewal order or gives written approval for a renewal period of one year or less.
- V4_round_trip_extra R-005 section 5: The section permits processing for purposes beyond Customer's documented instructions (i.e., to provide and support the services), falling short of the fallback's stricter 'only under Customer's documented instructions' standard, and thus violates the rule.
  Quote: Vendor will comply with laws applicable to Vendor's provision of the services.
- V4_round_trip_extra R-007 section 10: The section omits the fallback's requirement that each Order Form have an initial term of no more than one year. It states only that the initial term is as stated in the Order Form, leaving open the possibility of an initial commitment exceeding one year without the customer's explicit signed approval for that longer lock-in, which violates the rule's lock-in control principle.
  Quote: Each Order Form has the initial term stated in it and will not automatically extend unless Customer signs a renewal order or gives written approval for a renewal period of one year or less.

## tasks/generated/T2-MSA-106

- V3_clean_base R-005 section 5: The section allows processing for 'provide and support the services' and 'as otherwise expressly authorized in an Order Form' beyond Customer's documented instructions, which is less protective than the fallback requirement to process only under Customer's documented instructions.
  Quote: Vendor will process Customer Data only to provide and support the services, to comply with Customer's documented instructions, and as otherwise expressly authorized in an Order Form.
- V3_clean_base R-007 section 10: The section does not limit the initial term to one year, allowing Order Forms with longer commitments without the specific signed renewal approval required by the fallback, making it less protective.
  Quote: Each Order Form has the initial term stated in it and will not automatically extend unless Customer signs a renewal order or gives written approval for a renewal period of one year or less.
- V4_round_trip_extra R-006 section 11: The section fails to limit post-termination liability to undisputed amounts. It only requires payment of 'approved reimbursable expenses' without requiring they be undisputed, potentially imposing costs beyond the accrued, undisputed amounts required by R-006.
  Quote: Customer will pay fees for services performed before the effective termination date and approved reimbursable expenses incurred before that date.
- V4_round_trip_extra R-007 section 10: The section fails to limit the initial term of an Order Form to no more than one year, as required by the fallback. It only states the initial term is as stated in the Order Form, allowing a term longer than one year without customer's signed approval for a commitment exceeding one year, which violates the rule's requirement that lock-in control stays with the customer and longer commitments need signed approval.
  Quote: Each Order Form has the initial term stated in it and will not automatically extend unless Customer signs a renewal order or gives written approval for a renewal period of one year or less.

## tasks/generated/T2-NDA-102

- V3_clean_base R-012 section 12: The section contains a residual knowledge clause in violation of the rule that such clauses must be absent unless expressly approved by the client. The clause states it is only effective if 'the parties approve that right in a signed writing,' but the clause itself is present without the required client approval. The fallback requires deletion of the clause unless the client expressly approves it in writing.
  Quote: No right to use residual knowledge, unaided memory, or retained impressions is granted under this Agreement unless the parties approve that right in a signed writing.
- V4_round_trip_extra R-012 section 10: The section contains a residual knowledge clause allowing the receiving side to keep and apply generalized ideas, techniques, and know-how, which violates the rule requiring such clauses to be absent unless expressly approved by the client in writing.
  Quote: The receiving side may keep and apply generalized ideas, techniques, and know-how drawn from the other side's materials in later work.

## tasks/generated/T1-GOV-911

- V3_clean_base R-009 section 12: The section excludes securities issued 'with debt financing' broadly, whereas the fallback limits the exclusion to 'debt with equity features'. This broader exclusion is less protective of preemptive rights, constituting a genuine violation.
  Quote: excluding securities issued under equity incentive plans, as acquisition consideration, in strategic transactions, in equipment or lease financing, with debt financing, or in a public offering.

## 2026-07-09 — arguable unplanted span in MA instances (model-review finding)

The MA base template's section-9 indemnification cap lacked a fraud qualifier,
arguably conflicting with rule R-006's position (fraud claims must not be
limited) even though R-006's planted mutation targets section 10. Impact: on
seeded MA instances generated from the pre-fix base, an agent flagging the
unqualified cap under R-006 takes a precision penalty on an arguable span.
Found during clean-instance review (gpt-5.6-sol pass); base fixed 2026-07-09
by pure append (fraud carve-out sentence) in generator/bases/PB-MA-001.json.
Existing generated/held-out MA instances are frozen and retain the old text —
disposition (regenerate vs. accept as documented ambiguity) is a v0.2 call.
