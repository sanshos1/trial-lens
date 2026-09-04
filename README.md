# Trial Lens
## Research question
Does a published claim describe the outcome that the study originally said it would measure?

Trial Lens is a consistency-checking primitive for three submitted records. It does not estimate treatment efficacy or recommend care.

### Evidence design
| Index | Document role | Question it informs |
| --- | --- | --- |
| 0 | Registry entry | What endpoint was registered? |
| 1 | Protocol or analysis plan | How was that endpoint prespecified? |
| 2 | Results or publication | What was reported? |

The contract consumes three distinct HTTPS URLs, a trial identifier and a claim of at least 30 characters. Additional supplied URLs are sliced off rather than analyzed.

### Method
Call `file_assessment(i, trial_id, claim, sources)`, then `evaluate(i)`. Evaluation is permissionless and closes the assessment once. Use `get_assessment(i)` and `get_finding(i)` to retrieve the evidence references and finding.

Within a nondeterministic call, the leader reads the first 15,000 body units per source and proposes endpoint matches, conflicts and a verdict. Validators refetch the records, check their digests and independently assess the proposed verdict and matches. This is semantic review, not identical-model-output voting.

### Observed example
The synthetic TL-101 fixture names mobility change at week 12 as the registered and reported endpoint. The stored smoke result is SUPPORTED. The reported limitations still matter: the fixture is not a complete trial dataset and cannot establish clinical significance.

SUPPORTED, OVERSTATED, CONTRADICTED and INCOMPLETE describe consistency with the supplied material. They are not medical conclusions.

### Threats to validity
- Publishers, trial IDs and document dates are not authenticated by the URL check.
- Digests bind bounded fetched content, not the complete source publication.
- The validator does not independently bind the stored limitations or rationale.
- Endpoint entries are bounded strings, not a typed statistical evidence schema.
- Invalid model data or retrieval errors may abort evaluation.
- One successful network run is not an independent clinical validation.

### Reproducibility record

#### Materials and execution

[The evidence directory](materials/) contains the synthetic registry, protocol and results texts. [The recorded finding](runs/finding.json) preserves the source URLs, digests, claim and network transaction references.

For the mocked reproduction, install the packages listed in `requirements.txt` with `python -m pip install -r requirements.txt`; execute `python -m pytest validation/direct -q`. The separate static check is `genvm-lint study/assessment.py`. Passing these checks says nothing about clinical predictive accuracy.

For a network reproduction, review [experiments/smoke.py](experiments/smoke.py). It selects account 3 from an untracked `accounts.env` four directories above the repository, submits a fresh assessment and reads the stored finding. Adapt credential loading for a standalone clone. Never put real patient information or private keys into the example.

[runs/deployment.json](runs/deployment.json) records the source and evidence revisions. The recorded run used synthetic text; it was not an independent replication of a clinical trial.

[Source](study/assessment.py), [direct tests](validation/direct/test_contract.py), and [stored network finding](runs/finding.json) are available for inspection. Direct tests exercise the lifecycle, input guards and a forged digest, not clinical accuracy.

Deployment and network-run files are generated after execution; use the paths referenced above to inspect the current evidence.
