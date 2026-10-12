# Context and evidence contract

Use a UTF-8 JSON object with every field below explicit:

```json
{
  "importer": "cloud-external-legacy",
  "project_type": "company-managed",
  "intent": "create",
  "parent_scope": "in-file",
  "log_row_numbering": "unknown",
  "columns": {"id": 1, "parent": 2, "summary": 3},
  "delimiter": ","
}
```

Allowed values:
- importer: cloud-external-legacy, cloud-new, cloud-bulk-create, data-center, unknown
- project_type: company-managed, team-managed, unknown
- intent: create, update, mixed, unknown
- parent_scope: in-file, external-or-mixed, unknown
- log_row_numbering: unknown, data-record-1, header-record-1, physical-line-1

`columns` and `delimiter` are optional. Column overrides are positive 1-based positions, not target Jira field IDs. Supported roles: id, parent, key, summary, type. Omitted roles resolve only from a unique recognized header (Issue ID/Work item ID; Issue Key/Work item key; Parent/Parent ID; Summary; Issue Type/Work Type/WorkType). Ambiguous role headers stay unresolved. Headers otherwise remain intact, including valid repeated multivalue/custom-field names.

The CSV is never rewritten. Identifiers retain original strings, including leading zeros and whitespace. Leading/trailing whitespace differences may prevent exact matching; the script does not guess whether the importer trims them. Logical record 1 is the first data record, distinct from CSV header-inclusive records and physical lines. Multiline cells have a start/end physical-line range. Input limits: 20 MiB per file, 50,000 parsed data records and 50,000 log lines. Cascade paths retain at most 32 ancestors with the full distance and a truncation flag; repeated ancestor-error evidence is capped at eight line references. Python's strict CSV reader is not a complete Jira dialect validator. Files use UTF-8/UTF-8 BOM; alternate encodings require an explicit conversion of a copy.

## Supported log evidence

This is intentionally not a universal Jira parser.

- Public old-experience records have issue/work-item context with bracketed externalId and summary fields. External IDs match the selected source ID only as exact strings. Generated autoid values are not row numbers. Conflicting ID/summary references remain unresolved
- Quoted summary references and quoted Subtask names produce candidates only, even when unique. Duplicate summaries are ambiguous
- Explicit Issue ID / Work item ID and Issue key / Work item key markers with `:` or `=` are also supported for user-verified or annotated logs; ID values in that annotation must be quoted in full; bare ID tokens are deliberately unsupported. Those variants are synthetic test contracts, not claimed native Jira formats
- Explicit Row/CSV row/line numbers require a declared numbering convention. The new-importer CSV error log documents Row markers, but the numbering origin remains unverified. CSV-shaped logs are scanned linewise in this pilot; multiline/doubled-quote error cells may remain unresolved
- Counter grammar supports created/updated totals and skipped-of-total counts. Both `N of T` and `N out of T` skipped wording are accepted; the latter is a synthetic compatibility variant, not claimed as observed native Jira grammar. Repeated counter kinds are treated as ambiguous attempts; no automatic last-run selection. Missing counters are not silently zero-filled
- Section tracking stops the generic new-items-only phrase in Users/Components sections from becoming work-item mode evidence. Unscoped excerpts are merely prompts to inspect the actual work-item section

A parent-cascade hypothesis requires an unambiguous ID/key/declared-row match, explicit creation-failure text for an ancestor, an attributed parent error on a descendant, a complete structurally consistent CSV with no detected graph conflict, and the verified profile/in-file mapping. It never confirms causality or proposes field deletion. Generic import errors are not automatically promoted to fatal creation failures.

## Output and exit codes

`report.json`: version, input SHA-256 hashes, context, source identity/physical-line mapping, typed findings, redacted evidence, correlation coverage, counter reconciliation, review order and limits.

`report.md`: readable summary with evidence. Raw values are untrusted; render or share only after review.

0 = reports written; 2 = invalid context, unsupported log/context encoding or input size, unreadable inputs, or output-path conflict. CSV defects, including non-UTF-8 CSV encoding, return 0 with findings when a report can be written. No exit code certifies a successful or safe import. Existing output paths are refused.
