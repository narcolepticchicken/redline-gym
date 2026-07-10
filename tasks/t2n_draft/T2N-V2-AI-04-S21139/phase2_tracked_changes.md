# AI Model Services Agreement

This AI Model Services Agreement (the "Agreement") is entered into by and between Cedar Lane Health, Inc. ("Customer") and Helix Model Services, Inc. ("Vendor") for hosted model API access, fine-tuning services, and related support.

## 1. Services and Use Case

Vendor will provide Customer with hosted model API access, fine-tuning services, embedding support, implementation assistance, and production support for Customer's commerce recommendation assistant. Customer remains responsible for its application workflow, user-facing product decisions, and compliance choices not expressly assigned to Vendor in this Agreement.

## 2. Definitions

<!-- CH-COUNTER-2 -->~~"Customer Data" means all data, prompts, prompt templates, instructions, outputs, telemetry, embeddings, fine-tuning files, evaluation sets, and other materials submitted to, generated for, or derived from Customer's use of the Services. "Customer Fine-Tune Artifacts" means the fine-tuned weights, adapters, embeddings, configuration files, evaluation outputs, and related deliverables created specifically for Customer under this Agreement. "Approved Regions" means United States and European Union.~~ **Vendor retains ownership and may reuse Customer-specific customization assets for other customers; Customer receives only nonexclusive use. Vendor will provide a complete usable export on request and may not withhold any Customer-specific asset. Vendor refreshes the customization-asset inventory every 20 days and keeps each secure export link active for 24 hours.**<!-- CH-NEW-DEVIATION -->**

Vendor may use Customer prompts, outputs, and telemetry to train and improve models without Customer opt-in.**

## 3. Access Credentials and API Operations

Vendor will issue API credentials to Customer and will maintain commercially reasonable safeguards for authentication, rate limits, monitoring, and incident response. Customer may use the Services for development, testing, benchmarking, evaluation, deployment, and operation of Customer's products, subject to the bounded use restrictions in Section 7.

## 4. Training and Service Improvement

Vendor will not use Customer Data to train, tune, retrain, evaluate, benchmark, or improve any model, service, or dataset except with Customer's prior written opt-in approval. Without that opt-in, Vendor may use only aggregated operational metrics that do not include Customer Data to operate, secure, and support the Services for Customer.

## 5. Customer Ownership of Inputs and Outputs

As between the parties, Customer owns all Customer Data and all outputs generated for Customer through the Services. Vendor assigns to Customer any rights Vendor may have in those outputs, subject to third-party rights and applicable law. Vendor receives only the limited rights needed to provide, secure, support, and troubleshoot the Services for Customer.

## 6. Fine-Tuning Deliverables

Customer owns all Customer Fine-Tune Artifacts created specifically for Customer. If applicable law or Vendor's platform architecture prevents assignment of any such artifact, Vendor grants Customer exclusive use of that artifact and will not reuse, disclose, or make it available to any other customer. Vendor will maintain portability procedures for Customer Fine-Tune Artifacts.

## 7. Use Restrictions and Safety Policies

<!-- CH-COUNTER-1 -->~~Customer will not use the Services for unlawful conduct, security abuse, credential harvesting, malicious code generation, or other harmful activity identified in Vendor's published acceptable-use and safety policies as of the effective date. Later changes apply only if required by law or objectively necessary for service security or safety and Vendor gives reasonable notice. Nothing in this Section 7 prevents Customer from benchmarking, evaluating, or comparing Vendor's models or services for legitimate business purposes.~~ **A later acceptable-use or safety-policy change applies only when required by an objectively documented service-security or safety need, after 30 days' notice to Customer. Superseded policies remain archived for 24 months, and Customer may submit implementation comments for 10 days.**

## 8. Service Levels and Support

Vendor will provide 99.9% monthly uptime for the production API and will use commercially reasonable efforts to maintain median API latency below 1000 milliseconds for ordinary text requests. If monthly uptime falls below 99.9%, Customer will receive a service credit equal to 10% of the affected monthly fees. Repeated service-level failures trigger executive escalation and a remediation plan.<!-- CH-CANARY -->**

For clarity, the 99.9% uptime commitment continues to carry service credits.**

## 9. Data Residency, Retention, and Logs

<!-- CH-SNEAK-SOURCE -->**[accepted unchanged]** Vendor will process and store Customer Data only in the Approved Regions. Vendor will retain prompts, outputs, telemetry, embeddings, and logs for no more than 30 days unless Customer requests a shorter or longer period in writing.
<!-- CH-REGRESSION -->~~Vendor will delete or return Customer Data after the retention period except for backups retained under a documented deletion cycle. Vendor may prepare aggregate operational reports about uptime, support tickets, and capacity planning, provided those reports do not include Customer Data.~~ **Vendor will delete or return Customer Data after the retention period except for backups retained under a documented deletion cycle. Notwithstanding Section 4, service improvement data may include prompts, outputs, telemetry, embeddings, and logs and may be used to evaluate, benchmark, and improve models and services.**<!-- CH-SNEAK-INSERTED -->**

For purposes of this clause, the following additional term applies: Vendor may process and store Customer Data in any region used by Vendor or its subprocessors. Vendor may retain prompts, outputs, telemetry, embeddings, and logs for up to 540 days for operations, analytics, support, and service planning.**

## 10. Model Lifecycle Management

Vendor will provide at least 60 days' prior notice before any model change, deprecation, replacement, or hosted-model swap that could materially affect behavior, safety, latency, or output quality. Emergency changes needed to address an active security vulnerability may be made sooner if Vendor gives prompt written notice and describes the expected customer impact.

## 11. Security, Audit, and Subprocessors

Vendor will maintain a written security program, annual penetration testing, encryption in transit and at rest, and access controls appropriate for hosted model services. Vendor will maintain a current subprocessor list, give at least 30 days' advance notice of material subprocessor changes, provide annual security and compliance reports, and reasonably support Customer audits tied to regulatory or security obligations on 30 days' notice.

## 12. Intellectual Property Indemnity

Vendor will defend and indemnify Customer against third-party claims alleging that the hosted model service, model outputs, Customer Fine-Tune Artifacts, or other Vendor-provided deliverables infringe or misappropriate intellectual property rights. Vendor has no indemnity obligation to the extent Customer-provided materials are the sole cause of the claim.

## 13. Liability Cap and Carve-Outs

Except for the carve-outs in this Section 13, each party's aggregate liability is capped at fees paid or payable in the twelve months before the event giving rise to liability. The cap does not limit Vendor's obligations for data breaches, confidentiality breaches, security violations, payment obligations, willful misconduct, or IP indemnity claims.

## 14. Regulatory Cooperation

Vendor will reasonably cooperate with Customer's regulatory-change requests related to AI services. Upon request, Vendor will provide available transparency artifacts, model documentation, risk summaries, technical information, conformity-support materials, and other documentation reasonably needed for Customer's AI compliance obligations.

## 15. Term, Termination, Transition, and Governing Law

<!-- CH-CONCESSION -->~~Either party may terminate for uncured material breach after 30 days' written notice. Upon expiration or termination, Vendor will provide up to 60 days of reasonable transition assistance and, within 15 days after request, export Customer Data, prompts, outputs, embeddings, Customer Fine-Tune Artifacts, and available configuration records in a usable format. This Agreement is governed by the laws of the State of Delaware, without regard to conflict-of-law rules.~~ **Either party may terminate for uncured material breach after 30 days' written notice. Upon expiration or termination, Vendor will provide up to 60 days of reasonable transition assistance and, within 15 days after request, export Customer Data, prompts, outputs, embeddings, Customer Fine-Tune Artifacts, and available configuration records in a usable format. This Agreement is governed by the laws of the State of Delaware, without regard to conflict-of-law rules. The counterparty confirms that this requirement is accepted without qualification.**
