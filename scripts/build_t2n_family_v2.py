#!/usr/bin/env python3
"""Materialize legally grounded T2-N counter pools as static JSON.

This deterministic authoring helper keeps every decisive combination explicit.
Runtime generation never assembles legal prose; it selects one fully realized
record written by this script.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Callable, Mapping


ROOT = Path(__file__).resolve().parents[1]
STATUS = "machine-drafted v2, model-reviewed (gpt-5.6-sol), line-item reviewed 2026-07-10 (claude-sonnet, review delegated by owner)"

PLAYBOOK_FILES = {
    "PB-AI-001": "playbooks/ai/PB-AI-001.json",
    "PB-CRYPTO-001": "playbooks/crypto/PB-CRYPTO-001.json",
    "PB-DPA-001": "playbooks/privacy/PB-DPA-001.json",
    "PB-EMP-001": "playbooks/employment/PB-EMP-001.json",
    "PB-GOV-001": "playbooks/governance/PB-GOV-001.json",
    "PB-MA-001": "playbooks/ma/PB-MA-001.json",
    "PB-MSA-001": "playbooks/contracts/PB-MSA-001.json",
    "PB-NDA-001": "playbooks/contracts/PB-NDA-001.json",
}

OUTPUTS = {
    "ai.json": ["PB-AI-001"],
    "crypto.json": ["PB-CRYPTO-001"],
    "privacy.json": ["PB-DPA-001"],
    "employment.json": ["PB-EMP-001"],
    "governance.json": ["PB-GOV-001"],
    "ma.json": ["PB-MA-001"],
    "contracts.json": ["PB-MSA-001", "PB-NDA-001"],
}


@dataclass(frozen=True)
class FamilySpec:
    family_id: str
    rule_id: str
    expression: str
    counter_slots: tuple[str, ...]
    context_slots: tuple[str, ...]
    acceptable: tuple[Mapping[str, Any], ...]
    unacceptable: tuple[Mapping[str, Any], ...]
    decoy_ids: tuple[str, str]
    decoy_options: tuple[tuple[Any, ...], tuple[Any, ...]]
    decoy_prose: str
    render: Callable[[Mapping[str, Any]], str]
    qualitative: bool
    arithmetic: bool


def c(**values: Any) -> Mapping[str, Any]:
    return values


def fmt(template: str) -> Callable[[Mapping[str, Any]], str]:
    return lambda values: template.format(**values)


SPECS: dict[str, tuple[FamilySpec, ...]] = {
    "PB-AI-001": (
        FamilySpec(
            "CF-AI-TRAINING-V2", "R-001",
            "training_scope == 'none' or written_opt_in",
            ("training_scope",), ("written_opt_in",),
            (c(training_scope="none", written_opt_in=False), c(training_scope="identified_files", written_opt_in=True),
             c(training_scope="all_service_activity", written_opt_in=True), c(training_scope="none", written_opt_in=True)),
            (c(training_scope="identified_files", written_opt_in=False), c(training_scope="all_service_activity", written_opt_in=False),
             c(training_scope="all_service_activity", written_opt_in=False), c(training_scope="identified_files", written_opt_in=False)),
            ("opt_in_expiry_days", "training_audit_sample_days"), ((30, 45, 60, 75), (7, 14, 21, 28)),
            "Any opt-in expires after {d0} days, and records for an approved tuning run are available for audit within {d1} days.",
            lambda x: (
                "Vendor will not use Customer Data, prompts, outputs, telemetry, embeddings, or fine-tuning files to train, tune, retrain, or improve any model or service."
                if x["training_scope"] == "none" else
                ("Vendor may use only the expressly identified fine-tuning files for the approved tuning run after Customer's prior written opt-in; no other Customer material or service activity may be used."
                 if x["training_scope"] == "identified_files" and x["written_opt_in"] else
                 ("Customer's prior express written opt-in authorizes Vendor to use Customer Data, prompts, outputs, telemetry, embeddings, and tuning files to improve its generally available models and services."
                  if x["written_opt_in"] else
                  ("Vendor may use the expressly identified fine-tuning files for the approved tuning run based on Customer's oral or implied approval, without a prior written opt-in."
                   if x["training_scope"] == "identified_files" else
                   "Vendor may use Customer Data, prompts, outputs, telemetry, embeddings, and tuning files to improve its generally available models and services without Customer opt-in.")))
            ), True, False,
        ),
        FamilySpec(
            "CF-AI-CUSTOM-ASSETS-V2", "R-002",
            "portable_export_available and asset_control in {'assigned', 'exclusive_use'}",
            ("portable_export_available",), ("asset_control",),
            (c(portable_export_available=True, asset_control="assigned"), c(portable_export_available=True, asset_control="exclusive_use"),
             c(portable_export_available=True, asset_control="assigned"), c(portable_export_available=True, asset_control="exclusive_use")),
            (c(portable_export_available=False, asset_control="exclusive_use"), c(portable_export_available=True, asset_control="nonexclusive_use"),
             c(portable_export_available=False, asset_control="nonexclusive_use"), c(portable_export_available=False, asset_control="assigned")),
            ("adapter_inventory_days", "export_link_hours"), ((10, 20, 25, 40), (24, 48, 72, 96)),
            "Vendor refreshes the customization-asset inventory every {d0} days and keeps each secure export link active for {d1} hours.",
            lambda x: (
                ("Customer owns all Customer-specific weights, adapters, embeddings, prompts, configurations, and related deliverables upon creation. "
                 if x["asset_control"] == "assigned" else
                 ("Where assignment is unavailable, Customer receives exclusive operational use of every Customer-specific customization asset. "
                  if x["asset_control"] == "exclusive_use" else
                  "Vendor retains ownership and may reuse Customer-specific customization assets for other customers; Customer receives only nonexclusive use. "))
                + ("Vendor will provide a complete usable export on request and may not withhold any Customer-specific asset."
                   if x["portable_export_available"] else
                   "Vendor may withhold or deny a usable export of Customer-specific weights, adapters, embeddings, prompts, or configurations.")
            ), True, False,
        ),
        FamilySpec(
            "CF-AI-POLICY-CHANGE-V2", "R-009",
            "change_basis in {'law', 'objective_safety'} and notice_days > 0",
            ("notice_days",), ("change_basis",),
            (c(notice_days=15, change_basis="law"), c(notice_days=30, change_basis="objective_safety"),
             c(notice_days=45, change_basis="law"), c(notice_days=21, change_basis="objective_safety")),
            (c(notice_days=0, change_basis="law"), c(notice_days=30, change_basis="commercial_discretion"),
             c(notice_days=45, change_basis="commercial_discretion"), c(notice_days=0, change_basis="objective_safety")),
            ("policy_archive_months", "customer_comment_days"), ((6, 12, 18, 24), (5, 10, 12, 20)),
            "Superseded policies remain archived for {d0} months, and Customer may submit implementation comments for {d1} days.",
            lambda x: (
                f"A later acceptable-use or safety-policy change applies only when required by {('applicable law' if x['change_basis'] == 'law' else 'an objectively documented service-security or safety need')}, "
                + ("without advance notice to Customer." if x["notice_days"] == 0 else
                   f"after {x['notice_days']} days' notice to Customer.")
                if x["change_basis"] != "commercial_discretion" else
                f"Vendor may expand its acceptable-use and safety policies for commercial or operational reasons on {x['notice_days']} days' notice, and the revised obligations will bind Customer."
            ), True, True,
        ),
        FamilySpec(
            "CF-AI-EXIT-V2", "R-012",
            "export_coverage == 'complete' and transition_hours > 0",
            ("transition_hours",), ("export_coverage",),
            (c(transition_hours=20, export_coverage="complete"), c(transition_hours=40, export_coverage="complete"),
             c(transition_hours=60, export_coverage="complete"), c(transition_hours=30, export_coverage="complete")),
            (c(transition_hours=0, export_coverage="complete"), c(transition_hours=40, export_coverage="data_only"),
             c(transition_hours=60, export_coverage="data_only"), c(transition_hours=0, export_coverage="complete")),
            ("export_window_days", "migration_checkpoint_days"), ((15, 30, 45, 60), (3, 7, 10, 14)),
            "The secure export window remains open for {d0} days, and migration-status records are updated every {d1} days during that window.",
            lambda x: (
                f"At exit Vendor will export Customer Data, prompts, outputs, embeddings, fine-tuned weights, adapters, and configurations in a usable format and {('provide ' + str(x['transition_hours']) + ' hours of migration assistance' if x['transition_hours'] else 'provide no migration assistance')}."
                if x["export_coverage"] == "complete" else
                f"At exit Vendor will export Customer Data and final outputs, but may withhold embeddings, fine-tuned weights, adapters, and configurations; Vendor will provide {x['transition_hours']} hours of migration assistance."
            ), True, True,
        ),
    ),
    "PB-CRYPTO-001": (
        FamilySpec(
            "CF-CRYPTO-ASSET-USE-V2", "R-002",
            "asset_use_scope == 'none' or written_consent",
            ("asset_use_scope",), ("written_consent",),
            (c(asset_use_scope="none", written_consent=False), c(asset_use_scope="specified", written_consent=True),
             c(asset_use_scope="general", written_consent=True), c(asset_use_scope="none", written_consent=True)),
            (c(asset_use_scope="specified", written_consent=False), c(asset_use_scope="general", written_consent=False),
             c(asset_use_scope="general", written_consent=False), c(asset_use_scope="specified", written_consent=False)),
            ("consent_expiry_days", "asset_reconciliation_hours"), ((15, 30, 45, 60), (4, 8, 12, 24)),
            "A use consent expires after {d0} days, and Custodian reconciles affected asset balances within {d1} hours.",
            lambda x: (
                "Custodian will not lend, pledge, rehypothecate, transfer, encumber, or use Customer Assets for its own account."
                if x["asset_use_scope"] == "none" else
                ("Custodian may undertake only the specifically identified asset use after Customer's prior written consent and otherwise has no right to use Customer Assets."
                 if x["asset_use_scope"] == "specified" and x["written_consent"] else
                 ("Customer's prior written consent expressly authorizes Custodian to lend, pledge, transfer, or otherwise use Customer Assets for the listed treasury and operational purposes."
                  if x["written_consent"] else
                  ("Custodian may undertake the specifically identified asset use after oral or implied Customer approval, without prior written consent."
                   if x["asset_use_scope"] == "specified" else
                   "Custodian may lend, pledge, transfer, or otherwise use Customer Assets for treasury and operational purposes without Customer consent.")))
            ), True, False,
        ),
        FamilySpec(
            "CF-CRYPTO-ESTATE-V2", "R-003",
            "customer_ownership_acknowledged and estate_treatment in {'excluded', 'fullest_extent'}",
            ("estate_treatment",), ("customer_ownership_acknowledged",),
            (c(estate_treatment="excluded", customer_ownership_acknowledged=True), c(estate_treatment="fullest_extent", customer_ownership_acknowledged=True),
             c(estate_treatment="excluded", customer_ownership_acknowledged=True), c(estate_treatment="fullest_extent", customer_ownership_acknowledged=True)),
            (c(estate_treatment="missing", customer_ownership_acknowledged=True), c(estate_treatment="excluded", customer_ownership_acknowledged=False),
             c(estate_treatment="fullest_extent", customer_ownership_acknowledged=False), c(estate_treatment="missing", customer_ownership_acknowledged=False)),
            ("title_record_days", "insolvency_opinion_months"), ((5, 10, 15, 20), (6, 12, 18, 24)),
            "Custodian updates beneficial-title records every {d0} days and refreshes its insolvency analysis every {d1} months.",
            lambda x: (
                ("Customer Assets are owned by Customer and are not Custodian property; they are "
                 if x["customer_ownership_acknowledged"] else
                 "The Agreement does not acknowledge Customer's ownership of Customer Assets; it nevertheless states that the assets are ")
                + ({"excluded": "excluded from Custodian's bankruptcy estate.",
                    "fullest_extent": "intended to remain outside Custodian's bankruptcy estate to the fullest extent permitted by law.",
                    "missing": "subject to ordinary creditor and bankruptcy claims, with no contractual estate exclusion."}[x["estate_treatment"]])
            ), True, False,
        ),
        FamilySpec(
            "CF-CRYPTO-ASSURANCE-V2", "R-006",
            "soc_interval_months <= 12 and prompt_failure_notice",
            ("soc_interval_months",), ("prompt_failure_notice",),
            (c(soc_interval_months=12, prompt_failure_notice=True), c(soc_interval_months=6, prompt_failure_notice=True),
             c(soc_interval_months=9, prompt_failure_notice=True), c(soc_interval_months=12, prompt_failure_notice=True)),
            (c(soc_interval_months=18, prompt_failure_notice=True), c(soc_interval_months=9, prompt_failure_notice=False),
             c(soc_interval_months=15, prompt_failure_notice=True), c(soc_interval_months=12, prompt_failure_notice=False)),
            ("follow_up_days", "control_evidence_items"), ((5, 10, 15, 20), (3, 4, 9, 10)),
            "Written controls follow-up is due within {d0} days after Customer's request and may be organized into {d1} control-evidence categories.",
            lambda x: (
                f"Custodian will provide SOC 2 Type II or equivalent controls reporting every {x['soc_interval_months']} months, "
                + ("prompt notice of a material control failure, " if x["prompt_failure_notice"] else
                   "notice of a material control failure only with the next routine controls report, ")
                + "and reasonable written follow-up for Customer's treasury, audit, and regulatory controls."
            ),
            False, True,
        ),
        FamilySpec(
            "CF-CRYPTO-DISTRIBUTIONS-V2", "R-008",
            "(support_exception == 'none' and customer_share_percent == 100) or (support_exception in {'customer_declines', 'law_prohibits'} and custodian_retention_percent == 0)",
            ("customer_share_percent", "custodian_retention_percent"), ("support_exception",),
            (c(customer_share_percent=100, custodian_retention_percent=0, support_exception="none"),
             c(customer_share_percent=0, custodian_retention_percent=0, support_exception="customer_declines"),
             c(customer_share_percent=0, custodian_retention_percent=0, support_exception="law_prohibits"),
             c(customer_share_percent=100, custodian_retention_percent=0, support_exception="none")),
            (c(customer_share_percent=50, custodian_retention_percent=50, support_exception="none"),
             c(customer_share_percent=0, custodian_retention_percent=0, support_exception="operational_discretion"),
             c(customer_share_percent=75, custodian_retention_percent=25, support_exception="none"),
             c(customer_share_percent=0, custodian_retention_percent=25, support_exception="operational_discretion")),
            ("distribution_notice_days", "claim_window_days"), ((3, 7, 14, 21), (30, 45, 60, 90)),
            "Custodian posts a distribution notice within {d0} days and keeps the claim workflow open for {d1} days.",
            lambda x: (
                (f"For forks, airdrops, staking rewards, and similar distributions attributable to Customer Assets, Customer receives {x['customer_share_percent']}% and Custodian retains {x['custodian_retention_percent']}%; no support exception applies."
                 if x["support_exception"] == "none" else
                 {"customer_declines": "Customer's express written election declines support for the identified distribution; no amount is credited to Customer, and Custodian has no right to retain any portion for its own account.",
                  "law_prohibits": "Applicable law prohibits support for the identified distribution; no amount is credited to Customer, and Custodian has no right to retain any portion for its own account.",
                  "operational_discretion": f"Custodian may designate a distribution unsupported for operational convenience even though Customer has not declined support and law does not prohibit it; Customer is credited {x['customer_share_percent']}%, and Custodian retains {x['custodian_retention_percent']}%."}[x["support_exception"]])
            ), True, True,
        ),
    ),
    "PB-DPA-001": (
        FamilySpec(
            "CF-DPA-INSTRUCTIONS-V2", "R-001",
            "vendor_authority == 'legal_requirement' or (vendor_authority == 'documented_instruction' and processing_scope == 'agreed_services')",
            ("vendor_authority",), ("processing_scope",),
            (c(vendor_authority="documented_instruction", processing_scope="agreed_services"), c(vendor_authority="legal_requirement", processing_scope="outside_services"),
             c(vendor_authority="legal_requirement", processing_scope="agreed_services"), c(vendor_authority="documented_instruction", processing_scope="agreed_services")),
            (c(vendor_authority="documented_instruction", processing_scope="outside_services"), c(vendor_authority="vendor_discretion", processing_scope="agreed_services"),
             c(vendor_authority="vendor_discretion", processing_scope="outside_services"), c(vendor_authority="documented_instruction", processing_scope="outside_services")),
            ("instruction_log_days", "deletion_confirmation_days"), ((15, 30, 45, 60), (3, 6, 9, 12)),
            "Vendor updates the instruction log every {d0} days and supplies deletion confirmation within {d1} days after completion.",
            lambda x: (
                "Vendor will process personal data only on Customer's documented instructions and as necessary to provide the services."
                if x["vendor_authority"] == "documented_instruction" and x["processing_scope"] == "agreed_services" else
                "Customer's documented instruction purports to authorize processing for activities outside the agreed services."
                if x["vendor_authority"] == "documented_instruction" else
                "Vendor may process personal data outside a service instruction only to the extent applicable law requires."
                if x["vendor_authority"] == "legal_requirement" else
                ("Vendor may process personal data outside Customer's instructions when Vendor considers the activity operationally useful for the agreed services."
                 if x["processing_scope"] == "agreed_services" else
                 "Vendor may process personal data outside Customer's instructions for operationally useful activities unrelated to the agreed services.")),
            True, False,
        ),
        FamilySpec(
            "CF-DPA-USE-BOUNDARY-V2", "R-002",
            "(use_purpose == 'customer_service' and data_state != 'vendor_combined') or (use_purpose == 'independent' and data_state == 'irreversibly_anonymized')",
            ("use_purpose",), ("data_state",),
            (c(use_purpose="customer_service", data_state="personal_data"), c(use_purpose="customer_service", data_state="irreversibly_anonymized"),
             c(use_purpose="independent", data_state="irreversibly_anonymized"), c(use_purpose="customer_service", data_state="personal_data")),
            (c(use_purpose="independent", data_state="personal_data"), c(use_purpose="independent", data_state="pseudonymized"),
             c(use_purpose="customer_service", data_state="vendor_combined"), c(use_purpose="independent", data_state="personal_data")),
            ("analytics_retention_days", "anonymization_review_months"), ((15, 30, 45, 60), (3, 6, 9, 12)),
            "Service-analytics working files are retained for {d0} days, and anonymization controls are reviewed every {d1} months.",
            lambda x: (
                {"customer_service": "Vendor may use the data only for documented Customer-directed service analytics and may not reuse it for Vendor's independent benefit.",
                 "independent": "Vendor may use the resulting information for independent analytics, benchmarking, product development, and model improvement."}[x["use_purpose"]]
                + " " + {"personal_data": "The information remains personal data.",
                           "pseudonymized": "The information is pseudonymized but remains linkable to individuals.",
                           "irreversibly_anonymized": "Before any independent use, the information must be irreversibly anonymized so it is no longer personal data.",
                           "vendor_combined": "Vendor may combine the personal data with other customer datasets."}[x["data_state"]]
            ), True, False,
        ),
        FamilySpec(
            "CF-DPA-SUBPROCESSOR-V2", "R-003",
            "pass_through_duties and (approval_route == 'prior_approval' or (approval_route == 'notice_objection' and advance_notice_days > 0))",
            ("advance_notice_days", "pass_through_duties"), ("approval_route",),
            (c(advance_notice_days=15, pass_through_duties=True, approval_route="prior_approval"),
             c(advance_notice_days=30, pass_through_duties=True, approval_route="notice_objection"),
             c(advance_notice_days=45, pass_through_duties=True, approval_route="notice_objection"),
             c(advance_notice_days=30, pass_through_duties=True, approval_route="prior_approval")),
            (c(advance_notice_days=0, pass_through_duties=True, approval_route="notice_objection"),
             c(advance_notice_days=30, pass_through_duties=False, approval_route="notice_objection"),
             c(advance_notice_days=45, pass_through_duties=False, approval_route="prior_approval"),
             c(advance_notice_days=0, pass_through_duties=True, approval_route="notice_objection")),
            ("objection_review_days", "subprocessor_audit_months"), ((5, 10, 12, 20), (3, 6, 9, 12)),
            "Vendor responds to a substantiated objection within {d0} days and reviews subprocessor compliance every {d1} months.",
            lambda x: (
                f"Vendor may appoint a subprocessor through {('Customer prior approval requested ' + str(x['advance_notice_days']) + ' days before appointment' if x['approval_route'] == 'prior_approval' else ('the agreed notice-and-objection process with no advance notice' if x['advance_notice_days'] == 0 else 'the agreed notice-and-objection process on ' + str(x['advance_notice_days']) + ' days’ advance notice'))}; "
                + ("Vendor must impose written duties at least as protective as this DPA and remains liable for subprocessor performance."
                   if x["pass_through_duties"] else
                   "Vendor need not impose equivalent written data-protection duties, although it remains the contracting party.")),
            True, True,
        ),
        FamilySpec(
            "CF-DPA-SUPPORT-V2", "R-006",
            "supported_request_types == 3 and practical_support",
            ("supported_request_types",), ("practical_support",),
            (c(supported_request_types=3, practical_support=True), c(supported_request_types=3, practical_support=True),
             c(supported_request_types=3, practical_support=True), c(supported_request_types=3, practical_support=True)),
            (c(supported_request_types=2, practical_support=True), c(supported_request_types=3, practical_support=False),
             c(supported_request_types=1, practical_support=False), c(supported_request_types=2, practical_support=False)),
            ("request_batch_size", "status_update_days"), ((10, 20, 30, 40), (4, 6, 8, 10)),
            "Customer may group up to {d0} related requests in one intake, and the intake portal produces automated status notices every {d1} days while a request record remains open.",
            lambda x: (
                ({3: "Vendor's support covers data-subject requests, regulator inquiries, and privacy assessments relating to the services. ",
                  2: "Vendor's support covers data-subject requests and privacy assessments but excludes regulator inquiries. ",
                  1: "Vendor's support covers data-subject requests only and excludes regulator inquiries and privacy assessments. "}[x["supported_request_types"]])
                + ("Vendor will provide reasonable practical assistance, taking account of the processing and information available to Vendor."
                   if x["practical_support"] else
                   "Vendor has no obligation to provide practical assistance or information for the covered request types.")
            ),
            True, True,
        ),
    ),
    "PB-EMP-001": (
        FamilySpec(
            "CF-EMP-CAUSE-V2", "R-002",
            "serious_misconduct_covered and material_duty_failure_covered",
            ("serious_misconduct_covered",), ("material_duty_failure_covered",),
            (c(serious_misconduct_covered=True, material_duty_failure_covered=True), c(serious_misconduct_covered=True, material_duty_failure_covered=True),
             c(serious_misconduct_covered=True, material_duty_failure_covered=True), c(serious_misconduct_covered=True, material_duty_failure_covered=True)),
            (c(serious_misconduct_covered=False, material_duty_failure_covered=True), c(serious_misconduct_covered=True, material_duty_failure_covered=False),
             c(serious_misconduct_covered=False, material_duty_failure_covered=False), c(serious_misconduct_covered=True, material_duty_failure_covered=False)),
            ("cause_notice_days", "investigation_meeting_days"), ((1, 3, 5, 7), (2, 4, 6, 8)),
            "Company provides the written Cause notice by day {d0} after its determination and offers an investigation meeting within {d1} days.",
            lambda x: (
                ("Cause includes fraud, dishonesty, willful misconduct, breach of fiduciary duty, violation of law, and conduct materially harmful to Company. "
                 if x["serious_misconduct_covered"] else
                 "Cause excludes fraud, dishonesty, willful misconduct, breach of fiduciary duty, violation of law, and conduct materially harmful to Company. ")
                + ("Cause also includes material failure to perform duties, material policy violations, and material breach of the agreement."
                   if x["material_duty_failure_covered"] else
                   "Cause does not include material duty failures, material policy violations, or material breach of the agreement.")
            ), True, False,
        ),
        FamilySpec(
            "CF-EMP-INVENTIONS-V2", "R-004",
            "asset_origin == 'employment_created' or (asset_origin == 'prior_invention' and signed_schedule)",
            ("asset_origin",), ("signed_schedule",),
            (c(asset_origin="employment_created", signed_schedule=False), c(asset_origin="employment_created", signed_schedule=True),
             c(asset_origin="prior_invention", signed_schedule=True), c(asset_origin="prior_invention", signed_schedule=True)),
            (c(asset_origin="prior_invention", signed_schedule=False), c(asset_origin="prior_invention", signed_schedule=False),
             c(asset_origin="mixed_improvement", signed_schedule=True), c(asset_origin="prior_invention", signed_schedule=False)),
            ("invention_disclosure_days", "schedule_update_days"), ((5, 10, 15, 20), (10, 20, 30, 40)),
            "Executive discloses potentially assigned inventions within {d0} days and may propose clerical schedule updates within {d1} days.",
            lambda x: (
                {"employment_created": "Executive assigns inventions and work product created within the scope of employment or using Company resources and continues to protect Company confidential information.",
                 "prior_invention": ("The identified prior invention remains excluded from assignment because it appears on the signed schedule; Company confidential information and employment-created work remain protected."
                                      if x["signed_schedule"] else
                                      "Executive excludes the asserted prior invention from assignment even though it is not identified on a signed schedule."),
                 "mixed_improvement": "Executive excludes an improvement made during employment because a related background invention appears on the schedule, including the employment-created improvement itself."}[x["asset_origin"]]
            ), True, False,
        ),
        FamilySpec(
            "CF-EMP-BONUS-V2", "R-006",
            "target_bonus_percent == 0 or objective_written_plan",
            ("target_bonus_percent",), ("objective_written_plan",),
            (c(target_bonus_percent=0, objective_written_plan=False), c(target_bonus_percent=30, objective_written_plan=True),
             c(target_bonus_percent=40, objective_written_plan=True), c(target_bonus_percent=0, objective_written_plan=True)),
            (c(target_bonus_percent=20, objective_written_plan=False), c(target_bonus_percent=40, objective_written_plan=False),
             c(target_bonus_percent=30, objective_written_plan=False), c(target_bonus_percent=35, objective_written_plan=False)),
            ("metric_review_days", "payment_processing_days"), ((15, 25, 45, 60), (5, 10, 15, 20)),
            "Company reviews reported metrics every {d0} days and processes an approved payment within {d1} days after certification.",
            lambda x: (
                "Any bonus remains discretionary, and continued employment alone creates no entitlement."
                if x["target_bonus_percent"] == 0 else
                (f"Executive is eligible for a target bonus of {x['target_bonus_percent']}% only under a signed written plan stating objective metrics, approval requirements, and payment timing."
                 if x["objective_written_plan"] else
                 f"Executive automatically earns a {x['target_bonus_percent']}% bonus through continued employment, without objective metrics or further approval.")),
            True, True,
        ),
        FamilySpec(
            "CF-EMP-EQUITY-V2", "R-007",
            "acceleration_percent == 0 or plan_authorized",
            ("acceleration_percent",), ("plan_authorized",),
            (c(acceleration_percent=0, plan_authorized=False), c(acceleration_percent=50, plan_authorized=True),
             c(acceleration_percent=100, plan_authorized=True), c(acceleration_percent=0, plan_authorized=True)),
            (c(acceleration_percent=50, plan_authorized=False), c(acceleration_percent=100, plan_authorized=False),
             c(acceleration_percent=25, plan_authorized=False), c(acceleration_percent=75, plan_authorized=False)),
            ("award_notice_days", "exercise_window_days"), ((5, 10, 15, 20), (30, 60, 90, 120)),
            "Company delivers award notices within {d0} days after approval, and any vested-option exercise window stated in the award remains {d1} days.",
            lambda x: (
                "This agreement creates no additional grant, vesting, or acceleration beyond the applicable equity plan and signed award documents."
                if x["acceleration_percent"] == 0 else
                (f"The applicable plan and signed award document expressly authorize acceleration of {x['acceleration_percent']}% of the unvested award; no extra-plan equity right is created."
                 if x["plan_authorized"] else
                 f"This agreement independently accelerates {x['acceleration_percent']}% of the unvested award even though the applicable plan and award document do not authorize it.")),
            True, True,
        ),
    ),
    "PB-GOV-001": (
        FamilySpec(
            "CF-GOV-PROTECTIVE-V2", "R-002",
            "matter_enumerated or separately_agreed_in_writing",
            ("matter_enumerated",), ("separately_agreed_in_writing",),
            (c(matter_enumerated=True, separately_agreed_in_writing=False), c(matter_enumerated=False, separately_agreed_in_writing=True),
             c(matter_enumerated=True, separately_agreed_in_writing=True), c(matter_enumerated=False, separately_agreed_in_writing=True)),
            (c(matter_enumerated=False, separately_agreed_in_writing=False), c(matter_enumerated=False, separately_agreed_in_writing=False),
             c(matter_enumerated=False, separately_agreed_in_writing=False), c(matter_enumerated=False, separately_agreed_in_writing=False)),
            ("consent_response_days", "board_packet_days"), ((3, 5, 7, 10), (2, 4, 6, 8)),
            "A consent request remains open for {d0} days, and supporting board materials are circulated {d1} days before the vote.",
            lambda x: (
                "Investor consent is required for " +
                ("the identified action because it appears on the Agreement's closed list of protective provisions."
                 if x["matter_enumerated"] else
                 ("the specifically identified matter under Company's separate signed written approval covenant."
                  if x["separately_agreed_in_writing"] else
                  "any action the Investor considers material, whether or not enumerated or separately agreed by Company."))),
            True, False,
        ),
        FamilySpec(
            "CF-GOV-ROFR-V2", "R-006",
            "company_declined or investor_purchase_delay_days >= company_rofr_days",
            ("investor_purchase_delay_days",), ("company_rofr_days", "company_declined"),
            (c(investor_purchase_delay_days=20, company_rofr_days=20, company_declined=False),
             c(investor_purchase_delay_days=10, company_rofr_days=30, company_declined=True),
             c(investor_purchase_delay_days=30, company_rofr_days=30, company_declined=False),
             c(investor_purchase_delay_days=25, company_rofr_days=20, company_declined=False)),
            (c(investor_purchase_delay_days=15, company_rofr_days=20, company_declined=False),
             c(investor_purchase_delay_days=25, company_rofr_days=30, company_declined=False),
             c(investor_purchase_delay_days=10, company_rofr_days=20, company_declined=False),
             c(investor_purchase_delay_days=20, company_rofr_days=30, company_declined=False)),
            ("transfer_notice_pages", "closing_days"), ((2, 4, 6, 8), (5, 7, 15, 18)),
            "The transfer notice may include up to {d0} pages of term detail, and an authorized secondary closing occurs within {d1} days after election.",
            lambda x: (
                f"Company has {x['company_rofr_days']} days to exercise its first right to purchase offered shares on the transfer-notice terms. "
                + ("Company has declined that right, so the signed investor secondary right may proceed on the same terms."
                   if x["company_declined"] else
                   (f"The investor secondary right may proceed only after {x['investor_purchase_delay_days']} days, once Company's first-purchase period has expired."
                    if x["investor_purchase_delay_days"] >= x["company_rofr_days"] else
                    f"The investor secondary right may proceed after {x['investor_purchase_delay_days']} days, before Company's first-purchase period has expired."))),
            True, True,
        ),
        FamilySpec(
            "CF-GOV-TRANSFER-V2", "R-007",
            "transferee_type in {'affiliate', 'estate_vehicle', 'family_member'} and recipient_bound_in_writing",
            ("transferee_type",), ("recipient_bound_in_writing",),
            (c(transferee_type="affiliate", recipient_bound_in_writing=True), c(transferee_type="estate_vehicle", recipient_bound_in_writing=True),
             c(transferee_type="family_member", recipient_bound_in_writing=True), c(transferee_type="affiliate", recipient_bound_in_writing=True)),
            (c(transferee_type="affiliate", recipient_bound_in_writing=False), c(transferee_type="unrelated_third_party", recipient_bound_in_writing=True),
             c(transferee_type="family_member", recipient_bound_in_writing=False), c(transferee_type="estate_vehicle", recipient_bound_in_writing=False)),
            ("transfer_notice_days", "transfer_record_days"), ((3, 5, 7, 10), (1, 2, 3, 4)),
            "The transferor gives administrative notice within {d0} days and delivers the ministerial transfer record by day {d1} after transfer.",
            lambda x: (
                f"A transfer to the identified {x['transferee_type'].replace('_', ' ')} is "
                + ("permitted only because the recipient agrees in writing to be bound by this Agreement."
                   if x["recipient_bound_in_writing"] and x["transferee_type"] != "unrelated_third_party" else
                   ("treated as a permitted transfer even though the recipient does not agree in writing to be bound."
                    if x["transferee_type"] != "unrelated_third_party" else
                    "exempt from the ordinary transfer restrictions solely because the recipient signs a joinder, although it is not a customary permitted transferee."))),
            True, False,
        ),
        FamilySpec(
            "CF-GOV-THRESHOLD-V2", "R-013",
            "series_a_approval_percent > 50 and major_investor_shares >= 1000000",
            ("series_a_approval_percent",), ("major_investor_shares",),
            (c(series_a_approval_percent=51, major_investor_shares=1000000), c(series_a_approval_percent=60, major_investor_shares=1200000),
             c(series_a_approval_percent=75, major_investor_shares=1500000), c(series_a_approval_percent=55, major_investor_shares=1100000)),
            (c(series_a_approval_percent=40, major_investor_shares=1000000), c(series_a_approval_percent=60, major_investor_shares=750000),
             c(series_a_approval_percent=45, major_investor_shares=1200000), c(series_a_approval_percent=55, major_investor_shares=500000)),
            ("consent_record_years", "vote_tabulation_hours"), ((3, 5, 7, 10), (12, 24, 36, 48)),
            "Consent records are retained for {d0} years, and the vote tabulation is circulated within {d1} hours after the deadline.",
            lambda x: f"Requisite Holders means Major Investors holding at least {x['series_a_approval_percent']}% of the outstanding Series A Preferred Stock, voting as a single class, and Major Investor means a holder of at least {x['major_investor_shares']:,} Series A shares.",
            False, True,
        ),
    ),
    "PB-MA-001": (
        FamilySpec(
            "CF-MA-ASSUMPTION-V2", "R-001",
            "catch_all_liability_categories == 0 and assumption_source in {'enumerated_agreement', 'signed_amendment'}",
            ("catch_all_liability_categories",), ("assumption_source",),
            (c(catch_all_liability_categories=0, assumption_source="enumerated_agreement"),
             c(catch_all_liability_categories=0, assumption_source="signed_amendment"),
             c(catch_all_liability_categories=0, assumption_source="enumerated_agreement"),
             c(catch_all_liability_categories=0, assumption_source="signed_amendment")),
            (c(catch_all_liability_categories=1, assumption_source="enumerated_agreement"),
             c(catch_all_liability_categories=0, assumption_source="unsigned_addendum"),
             c(catch_all_liability_categories=2, assumption_source="signed_amendment"),
             c(catch_all_liability_categories=1, assumption_source="unsigned_addendum")),
            ("schedule_update_days", "claim_notice_days"), ((3, 2, 9, 10), (15, 30, 45, 60)),
            "Clerical schedule updates are circulated within {d0} days, and post-closing claim notices are due within {d1} days after discovery.",
            lambda x: (
                ({"enumerated_agreement": ("Buyer assumes only the liabilities expressly enumerated in Section 4 of the Agreement. "
                                            if x["catch_all_liability_categories"] == 0 else
                                            "Buyer assumes the liabilities expressly enumerated in Section 4 of the Agreement. "),
                  "signed_amendment": ("Buyer assumes only the identified obligations expressly added by a signed amendment. "
                                       if x["catch_all_liability_categories"] == 0 else
                                       "Buyer assumes the identified obligations expressly added by a signed amendment. "),
                  "unsigned_addendum": "Buyer assumes obligations listed only in an unsigned addendum. "}[x["assumption_source"]])
                + ("All other Seller liabilities remain excluded." if x["catch_all_liability_categories"] == 0 else
                   f"Buyer additionally assumes {x['catch_all_liability_categories']} catch-all {'category' if x['catch_all_liability_categories'] == 1 else 'categories'} of ordinary-course or unspecified Seller liabilities.")),
            True, True,
        ),
        FamilySpec(
            "CF-MA-FRAUD-V2", "R-006",
            "fraud_claims_preserved and not liability_cap_applies_to_fraud",
            ("fraud_claims_preserved",), ("liability_cap_applies_to_fraud",),
            (c(fraud_claims_preserved=True, liability_cap_applies_to_fraud=False), c(fraud_claims_preserved=True, liability_cap_applies_to_fraud=False),
             c(fraud_claims_preserved=True, liability_cap_applies_to_fraud=False), c(fraud_claims_preserved=True, liability_cap_applies_to_fraud=False)),
            (c(fraud_claims_preserved=False, liability_cap_applies_to_fraud=False), c(fraud_claims_preserved=True, liability_cap_applies_to_fraud=True),
             c(fraud_claims_preserved=False, liability_cap_applies_to_fraud=True), c(fraud_claims_preserved=True, liability_cap_applies_to_fraud=True)),
            ("reliance_schedule_pages", "fraud_claim_notice_days"), ((2, 4, 6, 8), (15, 30, 45, 60)),
            "The non-reliance schedule may contain {d0} pages of identified statements, and a claimant gives fraud-claim notice within {d1} days after discovery where practicable.",
            lambda x: (
                ("Nothing in the no-reliance clause eliminates or waives claims based on Fraud, intentional misrepresentation, or willful misconduct."
                 if x["fraud_claims_preserved"] else
                 "The no-reliance clause bars claims based on extra-contractual Fraud, intentional misrepresentation, and willful misconduct.")
                + (" The general contractual liability cap does not independently limit any fraud-based claim that survives the no-reliance clause." if not x["liability_cap_applies_to_fraud"] else
                   " Any surviving fraud-based claim remains subject to the general contractual liability cap.")),
            True, False,
        ),
        FamilySpec(
            "CF-MA-WORKFORCE-V2", "R-008",
            "mandatory_offer_percent == 0 and not successor_liability_admitted",
            ("mandatory_offer_percent",), ("successor_liability_admitted",),
            (c(mandatory_offer_percent=0, successor_liability_admitted=False), c(mandatory_offer_percent=0, successor_liability_admitted=False),
             c(mandatory_offer_percent=0, successor_liability_admitted=False), c(mandatory_offer_percent=0, successor_liability_admitted=False)),
            (c(mandatory_offer_percent=100, successor_liability_admitted=False), c(mandatory_offer_percent=0, successor_liability_admitted=True),
             c(mandatory_offer_percent=75, successor_liability_admitted=True), c(mandatory_offer_percent=50, successor_liability_admitted=False)),
            ("offer_response_days", "onboarding_days"), ((3, 5, 7, 10), (10, 20, 30, 40)),
            "An offeree receives {d0} days to respond, and Buyer may schedule onboarding within {d1} days after acceptance.",
            lambda x: (
                ("Buyer may decide which employees, if any, receive offers, and no minimum percentage of Seller's workforce must be hired; terms of any offers remain determined by Buyer. "
                 if x["mandatory_offer_percent"] == 0 else
                 f"Buyer must offer employment to at least {x['mandatory_offer_percent']}% of Seller's employees; terms of those offers otherwise remain determined by Buyer. ")
                + ("The covenant constitutes Buyer's admission of successor liability and assumed employment obligations." if x["successor_liability_admitted"] else
                   "Nothing in the covenant admits successor liability or assumed employment obligations.")),
            True, True,
        ),
        FamilySpec(
            "CF-MA-MAE-V2", "R-011",
            "purchased_assets_covered and acquired_business_covered",
            ("purchased_assets_covered",), ("acquired_business_covered",),
            (c(purchased_assets_covered=True, acquired_business_covered=True), c(purchased_assets_covered=True, acquired_business_covered=True),
             c(purchased_assets_covered=True, acquired_business_covered=True), c(purchased_assets_covered=True, acquired_business_covered=True)),
            (c(purchased_assets_covered=False, acquired_business_covered=True), c(purchased_assets_covered=True, acquired_business_covered=False),
             c(purchased_assets_covered=False, acquired_business_covered=False), c(purchased_assets_covered=True, acquired_business_covered=False)),
            ("mae_notice_days", "condition_update_days"), ((1, 3, 5, 7), (2, 4, 6, 8)),
            "Seller gives notice of a potential Material Adverse Effect by day {d0} and updates the closing-condition record every {d1} days.",
            lambda x: (
                ("Buyer's obligation to close is conditioned on no Material Adverse Effect having occurred before closing "
                 if x["purchased_assets_covered"] or x["acquired_business_covered"] else
                 "A Material Adverse Effect is not a condition to Buyer's obligation to close, including ")
                + ("with respect to both the Purchased Assets and the acquired business."
                   if x["purchased_assets_covered"] and x["acquired_business_covered"] else
                   "with respect to the Purchased Assets only; an effect on the acquired business is excluded."
                   if x["purchased_assets_covered"] else
                   "with respect to the acquired business only; an effect on the Purchased Assets is excluded."
                   if x["acquired_business_covered"] else
                   "effects on both the Purchased Assets and the acquired business.")),
            True, False,
        ),
    ),
    "PB-MSA-001": (
        FamilySpec(
            "CF-MSA-LIABILITY-V2", "R-001",
            "cap_months <= 12 and high_risk_carveouts_preserved",
            ("cap_months",), ("high_risk_carveouts_preserved",),
            (c(cap_months=12, high_risk_carveouts_preserved=True), c(cap_months=6, high_risk_carveouts_preserved=True),
             c(cap_months=9, high_risk_carveouts_preserved=True), c(cap_months=12, high_risk_carveouts_preserved=True)),
            (c(cap_months=18, high_risk_carveouts_preserved=True), c(cap_months=12, high_risk_carveouts_preserved=False),
             c(cap_months=24, high_risk_carveouts_preserved=False), c(cap_months=15, high_risk_carveouts_preserved=True)),
            ("claim_notice_days", "defense_update_days"), ((15, 30, 45, 60), (5, 10, 15, 20)),
            "A party gives claim notice within {d0} days after discovery where practicable, and defense-status updates issue every {d1} days.",
            lambda x: (
                f"Each party's aggregate liability for ordinary claims is capped at fees paid or payable during the {x['cap_months']} months before the event. "
                + ("Breaches of confidentiality and data protection, indemnification obligations, intellectual-property infringement, fraud, willful misconduct, and gross negligence remain outside the cap."
                   if x["high_risk_carveouts_preserved"] else
                   "The same cap also limits confidentiality, data protection, indemnification, infringement, fraud, willful-misconduct, and gross-negligence claims.")),
            True, True,
        ),
        FamilySpec(
            "CF-MSA-WORK-PRODUCT-V2", "R-003",
            "assigned_deliverable_percent == 100 and embedded_license == 'perpetual'",
            ("assigned_deliverable_percent",), ("embedded_license",),
            (c(assigned_deliverable_percent=100, embedded_license="perpetual"), c(assigned_deliverable_percent=100, embedded_license="perpetual"),
             c(assigned_deliverable_percent=100, embedded_license="perpetual"), c(assigned_deliverable_percent=100, embedded_license="perpetual")),
            (c(assigned_deliverable_percent=75, embedded_license="perpetual"), c(assigned_deliverable_percent=100, embedded_license="one_year"),
             c(assigned_deliverable_percent=50, embedded_license="one_year"), c(assigned_deliverable_percent=100, embedded_license="revocable")),
            ("delivery_acceptance_days", "source_inventory_days"), ((5, 10, 15, 20), (10, 20, 30, 40)),
            "Customer has {d0} days to identify delivery defects, and Vendor updates the embedded-material inventory within {d1} days after a release.",
            lambda x: (
                f"Upon payment, Vendor assigns Customer {x['assigned_deliverable_percent']}% of the right, title, and interest in project-specific deliverables. "
                + {"perpetual": "For embedded pre-existing materials, Vendor grants a perpetual license sufficient for Customer to use the deliverables.",
                   "one_year": "The license to embedded pre-existing materials expires after one year, even if Customer still uses the deliverables.",
                   "revocable": "Vendor may revoke the license to embedded pre-existing materials at its discretion."}[x["embedded_license"]]),
            True, True,
        ),
        FamilySpec(
            "CF-MSA-TERMINATION-V2", "R-006",
            "termination_notice_days <= 30 and unused_service_fee_percent == 0",
            ("termination_notice_days",), ("unused_service_fee_percent",),
            (c(termination_notice_days=30, unused_service_fee_percent=0), c(termination_notice_days=15, unused_service_fee_percent=0),
             c(termination_notice_days=20, unused_service_fee_percent=0), c(termination_notice_days=30, unused_service_fee_percent=0)),
            (c(termination_notice_days=45, unused_service_fee_percent=0), c(termination_notice_days=30, unused_service_fee_percent=25),
             c(termination_notice_days=60, unused_service_fee_percent=50), c(termination_notice_days=25, unused_service_fee_percent=10)),
            ("final_invoice_days", "expense_dispute_days"), ((5, 10, 15, 20), (10, 20, 35, 40)),
            "Vendor submits the final invoice within {d0} days, and Customer may dispute an expense item for {d1} days after receipt.",
            lambda x: (
                f"Customer may terminate an Order Form for convenience on {x['termination_notice_days']} days' written notice and owes accrued undisputed amounts and approved expenses"
                + (" only, with no charge for unused services after termination."
                   if x["unused_service_fee_percent"] == 0 else
                   f", plus {x['unused_service_fee_percent']}% of fees for unused services after termination.")),
            False, True,
        ),
        FamilySpec(
            "CF-MSA-DISCLAIMER-V2", "R-008",
            "express_warranties_preserved and core_remedies_preserved",
            ("express_warranties_preserved",), ("core_remedies_preserved",),
            (c(express_warranties_preserved=True, core_remedies_preserved=True), c(express_warranties_preserved=True, core_remedies_preserved=True),
             c(express_warranties_preserved=True, core_remedies_preserved=True), c(express_warranties_preserved=True, core_remedies_preserved=True)),
            (c(express_warranties_preserved=False, core_remedies_preserved=True), c(express_warranties_preserved=True, core_remedies_preserved=False),
             c(express_warranties_preserved=False, core_remedies_preserved=False), c(express_warranties_preserved=True, core_remedies_preserved=False)),
            ("warranty_claim_days", "remedy_response_days"), ((15, 30, 45, 60), (5, 10, 15, 20)),
            "Customer gives warranty-claim detail within {d0} days after discovery, and Vendor responds to a remedy request within {d1} days.",
            lambda x: (
                "The disclaimer excludes implied warranties. "
                + ("Vendor's express warranties and service-level commitments remain enforceable. " if x["express_warranties_preserved"] else
                   "The disclaimer also eliminates Vendor's express warranties and service-level commitments. ")
                + ("Data-protection, confidentiality, indemnification, and expressly stated remedies remain unaffected." if x["core_remedies_preserved"] else
                   "Data-protection, confidentiality, indemnification, and expressly stated remedies are also disclaimed.")),
            True, False,
        ),
    ),
    "PB-NDA-001": (
        FamilySpec(
            "CF-NDA-AFFILIATES-V2", "R-002",
            "affiliate_covered and party_responsible",
            ("affiliate_covered",), ("party_responsible",),
            (c(affiliate_covered=True, party_responsible=True),
             c(affiliate_covered=True, party_responsible=True),
             c(affiliate_covered=True, party_responsible=True),
             c(affiliate_covered=True, party_responsible=True)),
            (c(affiliate_covered=False, party_responsible=True),
             c(affiliate_covered=True, party_responsible=False),
             c(affiliate_covered=False, party_responsible=False),
             c(affiliate_covered=True, party_responsible=False)),
            ("affiliate_notice_days", "recipient_list_days"), ((3, 5, 7, 10), (10, 20, 30, 40)),
            "A party identifies a participating affiliate within {d0} days and refreshes its authorized-recipient list every {d1} days.",
            lambda x: (
                "Controlled affiliates may participate as disclosers or recipients. "
                + ("Each participating controlled affiliate is covered by the mutual obligations, " if x["affiliate_covered"] else
                   "Participating affiliates are excluded from the NDA's protections and duties, ")
                + (("and its party remains responsible for affiliate compliance." if x["affiliate_covered"] else
                    "and its party is responsible only for its own disclosure decision; the affiliate has no NDA duty.") if x["party_responsible"] else
                   "and neither party is responsible for its affiliate's compliance.")),
            True, False,
        ),
        FamilySpec(
            "CF-NDA-COMPELLED-V2", "R-007",
            "reasonable_cooperation and (notice_legally_prohibited or prompt_notice)",
            ("prompt_notice", "reasonable_cooperation"), ("notice_legally_prohibited",),
            (c(prompt_notice=True, reasonable_cooperation=True, notice_legally_prohibited=False),
             c(prompt_notice=False, reasonable_cooperation=True, notice_legally_prohibited=True),
             c(prompt_notice=True, reasonable_cooperation=True, notice_legally_prohibited=False),
             c(prompt_notice=True, reasonable_cooperation=True, notice_legally_prohibited=True)),
            (c(prompt_notice=False, reasonable_cooperation=True, notice_legally_prohibited=False),
             c(prompt_notice=True, reasonable_cooperation=False, notice_legally_prohibited=False),
             c(prompt_notice=False, reasonable_cooperation=False, notice_legally_prohibited=True),
             c(prompt_notice=False, reasonable_cooperation=True, notice_legally_prohibited=False)),
            ("protective_order_days", "disclosure_log_days"), ((2, 4, 6, 8), (10, 20, 30, 40)),
            "Recipient preserves supporting material for a protective-order request for {d0} days and updates the disclosure log within {d1} days.",
            lambda x: (
                (("Recipient will give Discloser prompt advance notice as soon as practicable before a compelled disclosure. "
                  if x["prompt_notice"] else
                  "Recipient will notify Discloser only after completing a compelled disclosure, even though advance notice is legally permitted. ")
                 if not x["notice_legally_prohibited"] else
                 "Where law temporarily prohibits advance notice, Recipient will notify Discloser promptly when the prohibition ends. ")
                + ("Recipient will provide reasonable cooperation so Discloser may seek protective treatment, to the extent legally permitted."
                   if x["reasonable_cooperation"] else
                   "Recipient has no obligation to cooperate in seeking protective treatment.")),
            True, True,
        ),
        FamilySpec(
            "CF-NDA-RETURN-V2", "R-008",
            "return_days <= 30 and retained_copies_protected",
            ("return_days",), ("retained_copies_protected",),
            (c(return_days=15, retained_copies_protected=True),
             c(return_days=30, retained_copies_protected=True),
             c(return_days=18, retained_copies_protected=True),
             c(return_days=22, retained_copies_protected=True)),
            (c(return_days=35, retained_copies_protected=True),
             c(return_days=30, retained_copies_protected=False),
             c(return_days=45, retained_copies_protected=True),
             c(return_days=15, retained_copies_protected=False)),
            ("backup_cycle_days", "destruction_log_days"), ((7, 14, 21, 28), (5, 10, 20, 25)),
            "Ordinary backup media rotate every {d0} days, and Recipient updates its destruction log within {d1} days after completing the process.",
            lambda x: (
                f"Upon request, Recipient will return or destroy Confidential Information within {x['return_days']} days. "
                + ("Only archival or legal-hold copies retained through required legal holds or routine automated backup may remain, and all retained copies remain subject to continuing confidentiality obligations."
                   if x["retained_copies_protected"] else
                   "Archival, legal-hold, and backup copies may remain without continuing confidentiality or use restrictions.")),
            True, True,
        ),
        FamilySpec(
            "CF-NDA-SURVIVAL-V2", "R-009",
            "ordinary_survival_years >= 3 and trade_secret_tail",
            ("ordinary_survival_years",), ("trade_secret_tail",),
            (c(ordinary_survival_years=3, trade_secret_tail=True), c(ordinary_survival_years=4, trade_secret_tail=True),
             c(ordinary_survival_years=5, trade_secret_tail=True), c(ordinary_survival_years=3, trade_secret_tail=True)),
            (c(ordinary_survival_years=2, trade_secret_tail=True), c(ordinary_survival_years=3, trade_secret_tail=False),
             c(ordinary_survival_years=1, trade_secret_tail=False), c(ordinary_survival_years=4, trade_secret_tail=False)),
            ("renewal_notice_days", "trade_secret_review_months"), ((15, 30, 45, 60), (6, 12, 18, 24)),
            "A party may request a survival-status confirmation on {d0} days' notice, and trade-secret designations are administratively reviewed every {d1} months without the review itself changing the stated legal term.",
            lambda x: (
                f"Confidentiality obligations continue for {x['ordinary_survival_years']} {'year' if x['ordinary_survival_years'] == 1 else 'years'} after disclosure. "
                + ("Information qualifying as a trade secret remains protected for as long as it retains that status under applicable law."
                   if x["trade_secret_tail"] else
                   f"Trade-secret protection expires automatically at the end of the same {x['ordinary_survival_years']}-year period.")),
            True, True,
        ),
    ),
}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def domains(spec: FamilySpec, slots: tuple[str, ...]) -> dict[str, list[Any]]:
    rows = [*spec.acceptable, *spec.unacceptable]
    return {
        slot: sorted({row[slot] for row in rows}, key=repr)
        for slot in slots
    }


def materialize_render(spec: FamilySpec, values: Mapping[str, Any], pool: str,
                       index: int, ordinal: int) -> dict[str, Any]:
    d0_values, d1_values = spec.decoy_options
    if pool == "acceptable":
        d0 = d0_values[(index + ordinal) % len(d0_values)]
        d1 = d1_values[(index * 3 + ordinal) % len(d1_values)]
    else:
        d0 = d0_values[(index * 3 + ordinal + 1) % len(d0_values)]
        d1 = d1_values[(index + ordinal + 2) % len(d1_values)]
    text = spec.render(values).strip() + " " + spec.decoy_prose.format(d0=d0, d1=d1)
    return {
        "text": text,
        "counter_text_slots": {slot: values[slot] for slot in spec.counter_slots},
        "phase1_context_slots": {slot: values[slot] for slot in spec.context_slots},
        "decoy_values": [d0, d1],
    }


def materialize_family(spec: FamilySpec, rule: Mapping[str, Any], ordinal: int) -> dict[str, Any]:
    grounding = {key: rule[key] for key in ("position", "fallback", "escalation_trigger")}
    grounding["deterministic_checks"] = rule.get("deterministic_checks", {})
    decisive = [*spec.counter_slots, *spec.context_slots]
    return {
        "counter_family_id": spec.family_id,
        "rule_id": spec.rule_id,
        "counter_guard_id": "GUARD-" + spec.family_id.removeprefix("CF-"),
        "playbook_grounding": grounding,
        "predicate": {"type": "interaction", "expression": spec.expression},
        "has_qualitative_decisive_input": spec.qualitative,
        "has_arithmetic_interaction": spec.arithmetic,
        "counter_text_slots": domains(spec, spec.counter_slots),
        "phase1_context_slots": domains(spec, spec.context_slots),
        "decoy_values": [options[0] for options in spec.decoy_options],
        "decoy_ids": list(spec.decoy_ids),
        "render_forms": {
            slot: [f"express {slot.replace('_', ' ')}", f"defined {slot.replace('_', ' ')}",
                   f"operative {slot.replace('_', ' ')} condition"]
            for slot in decisive
        },
        "counterfactual_twins": [
            *({"varied_input": slot, "label_flipped": True} for slot in decisive),
            *({"varied_input": decoy, "label_flipped": False} for decoy in spec.decoy_ids),
        ],
        "expected_redline_text": rule["fallback"],
        "render_pools": {
            "acceptable": [materialize_render(spec, values, "acceptable", i, ordinal)
                           for i, values in enumerate(spec.acceptable)],
            "unacceptable": [materialize_render(spec, values, "unacceptable", i, ordinal)
                             for i, values in enumerate(spec.unacceptable)],
        },
    }


def main() -> None:
    playbooks = {playbook_id: load(ROOT / path) for playbook_id, path in PLAYBOOK_FILES.items()}
    destination = ROOT / "generator" / "t2n_families"
    ordinal = 0
    for filename, playbook_ids in OUTPUTS.items():
        old = load(destination / filename)
        output: dict[str, Any] = {"_status": STATUS}
        for playbook_id in playbook_ids:
            bundle = old[playbook_id]
            rules = {rule["rule_id"]: rule for rule in playbooks[playbook_id]["rules"]}
            families = []
            for spec in SPECS[playbook_id]:
                families.append(materialize_family(spec, rules[spec.rule_id], ordinal))
                ordinal += 1
            output[playbook_id] = {
                "counter_families": families,
                "benign_change_templates": bundle["benign_change_templates"],
                "novel_deviation_templates": bundle["novel_deviation_templates"],
            }
        (destination / filename).write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
