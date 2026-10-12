# Pilot evaluation and release gate

Evaluation date: 12 October 2026. Runtime actually tested: Python 3.12.14, Linux. Claimed minimum Python 3.10 follows the used language features; 3.10 itself has not been run. No Jira account, import, private input, upload, public repository, or promotion was used for this pilot.

## Results actually observed

- 61 standard-library unittest cases pass (56 core diagnostics + 5 package-validation checks), including duplicate multivalue headers, opaque/leading-zero IDs, multiline CSV line ranges, ambiguous/no-match log references, generated IDs, counter ambiguity, token/email redaction, original-byte immutability, output overwrite refusal, and bounded cascade traces
- The bundled `scripts/validate_skill.py` verifies required name/description frontmatter, installed relative resources, and the reviewed runtime import allowlist without third-party packages. Five tests cover valid/missing metadata, broken relative links, network imports and dynamic execution. Skill-creator metadata/scaffold validation also passes; neither proves agent behavior
- Isolated project-shaped copies under `.claude/skills/jira-import-doctor` and `.agents/skills/jira-import-doctor` both validate the installed copy and run its CLI from a separate working directory under a socket/subprocess-denying audit guard, yielding expected artifacts. The guard confirms no network/process operation occurred in that execution; it is not a full security audit
- Actual Claude Code/Codex discovery, triggering, clean-host dependency setup and multi-version compatibility are **not tested** by that smoke. Claude Code is absent from the available environment; no host-side settings were changed
- The same deterministic engine with the log withheld vs included is reproducible with `python3 scripts/evaluate.py`. The full compact observed output is [evaluation-results.json](evaluation-results.json)

The ablation yields:

| Synthetic case | CSV-only result | Increment from the log |
|---|---|---|
| Graph errors | Duplicate ID, orphan, self-parent, cycle | None; existing preflight already covers this job |
| Cascade hypothesis | No definite local file defect | Three exact-ID error links and two possible ancestor/descendant cascades, with line evidence |
| Platform ambiguous | No definite local file defect | A possible importer signature, one summary candidate, reported 2 creations and 0 updates; no invented failed row |

This demonstrates a concrete extra input-to-output capability. It is **not** a measurement of agent quality, time saved, live import success, or superiority over another product. No fabricated percentage or with/without-agent score is reported.

## Real public attachment check

The [public JRACLOUD-96848 CSV](https://jira.atlassian.com/secure/attachment/512694/251202-import.csv) and [matching log](https://jira.atlassian.com/secure/attachment/512695/import-error.log) were retrieved without authentication and run through the actual helper. The package does not redistribute their full contents.

Observed: 2 CSV records, no definite file defects, one summary-only candidate warning, a profile-scoped known-importer signature, 2 reported creations and 0 updates. Skipped count is absent, so reconciliation remains incomplete. No cascade or whole-row creation failure was invented. Aggregate creation success cannot establish the parent link.

Input SHA-256:
- CSV: bbaf5a6394b0e4cd2089b336a42e6af526383c867e75896b5c5e4c2f32aeb0c3
- Log: a0f9d8ab22ef9472a41c1309d531d8ba9727d5fdaa83b05519d0adde5cb65d85

The 316-item public bulk-update report is separately covered by a synthetic test of its observed counter grammar/numbers. The test creates 316 fictional rows and verifies 270 + 0 + 46 arithmetic; it does not reconstruct the author's unavailable CSV or identify which actual items changed.

## Independent review

An independent reviewer ran all three cases and adversarial inputs. Initial review found quoted-ID truncation, unsafe graph attribution, missing-ID mapping certainty, confusion between comment and issue creation failures, Markdown/HTML injection risk, and quadratic ancestor traces. These were treated as release-blocking defects and fixed with regressions. Do not describe the initial passing 38-test suite as proof the pilot was sound. Final retest passed all 54 package tests and 20 independent adversarial checks. Both copy/run smokes passed again. No remaining blocking defect was found within that review scope. Native-format chain checks at 1,000 / 2,000 / 4,000 records took about 0.25 / 0.49 / 0.98 seconds, with traces capped at 32; these are local observations, not a general performance guarantee. The helper SHA-256 at that original review checkpoint was `28b79cd9463298a1ad81eb7e9bf0083d616458d68e4809559d4693bd9f56d9d6`.

## Narrow compatibility correction after the initial review

A held-out synthetic case exposed an honest coverage miss: the original parser recognized skipped counters using `N of T`, but omitted the variant `N out of T`. The initial missed-case observation is retained in the external evaluation rather than rescored as an original success. The parser now supports both forms. Two regressions verify arithmetic reconciliation without row/destination inference and continued ambiguity when both forms repeat a counter. This is a synthetic compatibility extension, not new evidence of native Jira grammar or agent superiority. After the fix, all seven frozen task cases passed a separate retest: exact matches and intended non-attributions remained correct, all three counter situations passed, and no unsupported definite diagnosis appeared. The public JRACLOUD-96848 parsed JSON was unchanged. All 21 test-input files remained unchanged. This is a regression recheck after feedback, not an unseen-test accuracy result. The current helper SHA-256 is `14088668a701dec59289ca219e5dd1966ea1d8153034316d0469e63a12af13a9`.

## Fair baseline comparison

[Preflight Lab's documented checklist](https://jira.preflightlab.tech/guide) already covers graph defects, intent, mapping, CSV structure and multiple destination-dependent risks. This pilot does not improve the graph-errors case and omits much of its date, attachment and field-normalization coverage. No user or private files were uploaded to it, and no direct live-service result comparison was performed.

The narrower addition is deterministic correlation between one failed attempt's evidence and the exact input, conservative cascade hypotheses, and partial-result accounting. A plain capable agent could also reason correctly about these small examples. One fresh seven-case comparison with a separate plain-agent pass has now been run. It was not controlled, blinded, randomized, or statistically meaningful: the scorer had read this package, authored the cases, and supplied domain assumptions to the plain agent. There is no basis for claiming higher diagnosis accuracy. Reproducibility and line/record traceability are observable properties, not proof of adoption.

In the initial comparison, both approaches made all four expected exact links, avoided all six forbidden attributions, preserved opaque IDs and repeated headers, and produced no unsupported definite diagnosis. The plain agent understood all three count situations; the CLI initially handled two, safely missing the synthetic skipped-counter variant described above. That miss was fixed after feedback. The retest does not turn the original result into an accuracy win. No competing online service was executed, and no live Jira result or time-saving measure was collected.

The copied-skill workflow also passed paths containing spaces, output-overwrite refusal and recovery, missing-input and invalid-context correction, and deliberately empty-log analysis. These are executable-workflow results, not host auto-discovery.

## Alpha release versus stronger claims

**GO: a bounded experimental read-only artifact for supervised local feedback**, subject to final review. A real-user trial needs an accessible artifact. The absence of that trial alone is not a reason to block an accurately labeled alpha.

Actual false attribution, unsupported certainty, input mutation, secret disclosure, unsafe report rendering, and unbounded resource growth are correctness/safety blockers, not acceptable alpha disclaimers. The reproduced blockers above were fixed and retested; new ones must likewise be resolved before release.

The following remain evidence limitations and must accompany any alpha description:
1. Real host auto-discovery/triggering has not been exercised; copy/run validation is a narrower result
2. No recurring importer has yet validated a next useful decision using a consented real CSV/log pair
3. The small plain-agent comparison showed no accuracy advantage; a fair competing-product comparison has not been executed
4. No Jira destination or live-import outcome is verified

Before making stronger readiness or superiority claims, test those exact claims on permitted inputs and record false attributions as well as correct abstentions. If real trials show no material value, improve an existing workflow instead of expanding this package. Stars measure attention, not import reliability or product-market fit.
