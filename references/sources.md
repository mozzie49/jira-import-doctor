# Verified sources and boundaries

Checked 12 October 2026. These are primary documentation/public reports, not proof of customer adoption of this pilot. Public text was inspected; no private Jira access or file upload occurred.

## Official CSV semantics

[Atlassian CSV import documentation](https://support.atlassian.com/jira-cloud-administration/docs/import-data-from-a-csv-file/) supports repeated multivalue headers, quoted multiline cells, import-local IDs, and mapped destination keys for updates. Its update example deliberately repeats keys and has blank Summary cells. Therefore this pilot avoids the generic unique-header rule, preserves string IDs, and only treats empty Summary as a definite defect in declared create intent. A configured source column can have another header; explicit positional overrides represent that mapping. This documentation is not a validation of every route or destination.

[Parent-child mapping KB](https://support.atlassian.com/jira/kb/keep-issue-parent-child-mapping-during-csv-import-to-jira-cloud/) is Cloud/company-managed guidance for the legacy external-system route. It uses unique import-local numeric identifiers and Parent references, with parent-first ordering recommended. The pilot checks exact relationships without coercing numeric strings, and treats ordering as review rather than guaranteed failure. It does not generalize this contract to Data Center, team-managed, or every new importer.

## Real public failure evidence

[Joshua Stokes's bulk-update report](https://community.atlassian.com/forums/discussion/3285098/unable-to-bulk-update-work-items) describes a previously working monthly process, three retries, and 270 skipped / 0 created / 46 updated out of 316. No final fix is established. Those aggregate counters reconcile arithmetically but cannot identify individual affected source rows. The regression is not proved merely because the process used to work.

[External issue-ID reuse KB](https://support.atlassian.com/jira/kb/csv-import-error-issues-have-been-skipped-because-they-already-exist-in-destination-projects/) describes a known skip cause. Its suggested destination mutation is outside this pilot. The script links the explanation without diagnosing the user's instance or clearing IDs.

[CTabeson's parent-validation report](https://community.atlassian.com/forums/discussion/3287144/import-project-w-csv-validation-error-issue-doesnt-have-a-valid-parent) has conflicting replies about IDs/mapping and an unconfirmed suggestion that an assignee problem prevents a parent from being created. Its validation screenshot was unavailable (CDN returned 403), so no exact screenshot transcription is claimed. The cascade example is synthetic, not a reconstruction or demonstrated resolution of this case.

[JRACLOUD-96848](https://jira.atlassian.com/browse/JRACLOUD-96848) was unresolved when checked. Its public [CSV attachment](https://jira.atlassian.com/secure/attachment/512694/251202-import.csv) and [log attachment](https://jira.atlassian.com/secure/attachment/512695/import-error.log) were successfully retrieved and examined. The CSV has two rows and a valid local parent edge. The log reports two creations despite an Epic Link field warning. The warning is summary-only and precedes the corresponding import record; attributing by the preceding row or treating every warning as a failed creation would be wrong. A key-shaped CustomField value is not a source key. The package includes only a labeled synthetic adaptation; local evaluation separately used the public attachments.

[JRACLOUD-95235](https://jira.atlassian.com/browse/JRACLOUD-95235) and [JRACLOUD-67325](https://jira.atlassian.com/browse/JRACLOUD-67325) establish error records with explicit bracketed externalId and summary fields. Generated IDs need not match any CSV column. [JRACLOUD-81974](https://jira.atlassian.com/browse/JRACLOUD-81974) shows generated IDs can change between validation and import. They cannot be decoded into source-row indexes.

[JRACLOUD-81997](https://jira.atlassian.com/browse/JRACLOUD-81997) provides a summary-only parent-validation format; summaries yield candidates only. [JRACLOUD-97429](https://jira.atlassian.com/browse/JRACLOUD-97429) documents a CSV-shaped newer-importer error log with Row markers, but does not establish numbering origin or multiline behavior. Raw row references require a declared convention; this pilot does not claim full support for that log dialect.

## Existing baseline

[Preflight Lab's guide](https://jira.preflightlab.tech/guide), reviewed on its site August 11, already covers intent, Summary/mapping, CSV shape, blank headers, ID/key distinction, parent graph defects, row order, destination-dependent values, dates, users, attachment URLs, and post-import reconciliation. It reports live-import observations and expressly limits what file checks can know about Jira. This pilot is narrower in dates/attachments/field normalization and does not claim a better CSV validator. Its testable addition is attempt-log evidence and conservative source correlation. No file was sent to that service and no side-by-side product benchmark was run.

## Host layout

[Codex skill documentation](https://developers.openai.com/codex/skills/) documents project `.agents/skills` discovery. [Claude Code skill documentation](https://code.claude.com/docs/en/skills) documents project `.claude/skills` and SKILL.md. The package copy-and-run smoke verifies those layouts and relative resources, not live agent discovery or automatic triggering.
