# T2-N design record

Reading order: spec_v2_architecture -> spec_v3_deltas -> reward_contract_v4
(authoritative for scoring; supersedes v3 §2). The three review_round files are
the adversarial record that shaped each revision; round 3 forced the role
inversion in which the reviewer authored the v4 contract against its own
attacks. Implementation: schema/t2n/, scoring/t2n_contract.py,
validators/t2n_checks.py, tests/test_t2n_*.
