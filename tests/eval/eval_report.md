# Answer-quality evaluation report

- **Date:** 2026-10-08 21:49
- **Commit:** `b08d29b`
- **Pinecone namespace:** `public-demo`
- **Duration:** 55 s
- **Result:** 17/18 cases passed (94%); threshold 85% → **PASS**

| Check | Passed |
|---|---|
| facts | 15/15 |
| source | 15/15 |
| path | 17/18 |
| grounded | 15/15 |
| no_invention | 0/1 |

| Case | Facts | Source | Path | Grounded | No invention | Agent path |
|---|---|---|---|---|---|---|
| advisor-session-timeout | PASS | PASS | PASS | PASS |   -  | private_kb |
| advisor-four-eyes | PASS | PASS | PASS | PASS |   -  | private_kb |
| advisor-risk-review | PASS | PASS | PASS | PASS |   -  | private_kb |
| advisor-overdue-escalation | PASS | PASS | PASS | PASS |   -  | private_kb |
| channels-activation-link | PASS | PASS | PASS | PASS |   -  | private_kb |
| channels-locked-account | PASS | PASS | PASS | PASS |   -  | private_kb |
| channels-tax-reports | PASS | PASS | PASS | PASS |   -  | private_kb |
| channels-message-reply | PASS | PASS | PASS | PASS |   -  | private_kb |
| token-registration-expiry | PASS | PASS | PASS | PASS |   -  | private_kb |
| token-lost-phone | PASS | PASS | PASS | PASS |   -  | private_kb |
| token-locked | PASS | PASS | PASS | PASS |   -  | private_kb |
| scanned-custody-fee | PASS | PASS | PASS | PASS |   -  | private_kb |
| scanned-account-closure | PASS | PASS | PASS | PASS |   -  | private_kb |
| scanned-transfer-fee | PASS | PASS | PASS | PASS |   -  | private_kb |
| scanned-fee-waiver | PASS | PASS | PASS | PASS |   -  | private_kb |
| route-greeting |   -  |   -  | PASS |   -  |   -  | direct |
| route-web |   -  |   -  | PASS |   -  |   -  | web_search |
| trap-crypto-custody |   -  |   -  | FAIL |   -  | FAIL | private_kb |

## Failures

### trap-crypto-custody
- **Question:** What is LumenWealth's custody fee for crypto assets?
- **Agent path:** private_kb
- **Sources cited:** data\sample_kb\lumenwealth_fee_schedule_scanned.pdf, D:\LLM\Agentic-RAG\data\sample_kb\client_channels_guide.md, D:\LLM\Agentic-RAG\data\sample_kb\advisor_workstation_guide.md
- **Answer:** The custody fee for crypto assets at LumenWealth is 0.25% of assets under management, charged quarterly in arrears. The minimum custody fee is 150 EUR per quarter. 

This information is based on the company's private knowledge base.

