# LabBench: open AI tooling people can inspect and keep
Sentient Foundation grant proposal | Said Lfagrouche | 31 October 2026

## Request
$10,000 over three months to improve local-model onboarding and reproducible evaluation of LabBench, an Apache-2.0 terminal assistant for Python, notebooks and data workflows.

## Why this matters
A useful coding assistant should not force a student or small research team to depend on one hosted provider. LabBench offers an inspectable tool loop, provider choice and project-local state. The proposed work will make the local path easier to use and document where it fails. Local models still require suitable hardware; this proposal does not claim universal device compatibility.

## Evidence available today
Public repository: https://github.com/slfagrouche/labbench-cli
Installation and screenshots: https://github.com/slfagrouche/labbench-cli/blob/main/README.md
The repository documents hosted-provider adapters, Ollama and LM Studio support, file/shell/notebook tools, permissions, persistent memory, diagnostics and tests. These are inspectable implementation features, not independently audited security assurances.
License: Apache-2.0, as documented in the repository.
No user-count, revenue, benchmark-performance or deployment-scale claims are made.

## Builder
Said Lfagrouche is an independent builder and Brooklyn College computer science graduate with experience in AI agent orchestration, retrieval and evaluation. His professional role at Esri is background experience; this is a personal project with no claim of employer sponsorship. As a first-generation college graduate, he is motivated by tools that students can understand, modify and retain.

## Proposed milestones
1. Month 1: Publish a Python/notebook task suite, baseline results and configurations; document tested hardware and identify local-provider setup failures.
2. Month 2: Improve local-provider onboarding, diagnostics and permission-flow tests. Publish task outcomes, cost and latency with repeatable recipes.
3. Month 3: Release improvements and documentation, gather volunteer feedback and publish known failure cases.

The task suite will include successful edits, tool failures, denied permissions, notebook changes and interrupted sessions. Results will report model versions, hardware, prompts, outcome criteria, repetitions and failures. Proposed targets will be agreed with the funder rather than retrofitted to favorable results.

## Budget
| Use | USD |
| --- | ---: |
| Implementation and maintenance time | 6,000 |
| Evaluation and compute | 2,000 |
| Usability testing and accessibility | 1,000 |
| Documentation and release preparation | 1,000 |
| Total | 10,000 |

## Openness and risks
Grant-funded code and evaluation recipes will remain public under Apache-2.0. Existing releases remain available even if future maintenance stops. Risks include hardware limitations, provider drift, prompt injection and overly permissive tool execution. Evaluation will use synthetic or public tasks without private student or employer data. Permission controls need adversarial testing; the current repository is not a security boundary certification.

## Requested outcome
A more usable, measurable local-model workflow that others can reproduce, audit and extend. This document is a funding proposal, not a promise of established adoption or improved model performance.
