# Fixture provenance and reuse

The project’s original code, documentation and synthetic fixtures are licensed under the [MIT License](../LICENSE), copyright 2026 mozzie49. That grant does not cover third-party Atlassian materials or their trademarks.

- The implementation, skill instructions, and synthetic CSV fixtures were created for this project. No third-party source-code implementation was copied into the package
- Every bundled `examples/*/input.csv` and `examples/*/import.log` is fictional. Some logs use observed Jira protocol/error grammar with invented identities, explicitly labeled synthetic. They are not customer files, transcripts of unavailable screenshots, or proof of a successful Jira run
- `examples/reports/` is generated from those synthetic fixtures by `scripts/render_demos.py`; before and after mean evidence withheld/included, not a CSV repair or successful re-import
- No permission or redistribution license for Atlassian attachments is assumed. Their complete CSV/log files are not included. The evaluation records attributed observations and hashes, rather than redistributing those files
- The source links below remain subject to Atlassian's terms. Download only the named public files through their official pages if you choose to reproduce the check; do not work around access restrictions
- This diagnostic project is independent of Atlassian and is not endorsed by it

## Optional public-source reproduction

1. Open [JRACLOUD-96848](https://jira.atlassian.com/browse/JRACLOUD-96848)
2. Download the linked [CSV attachment](https://jira.atlassian.com/secure/attachment/512694/251202-import.csv) and [log attachment](https://jira.atlassian.com/secure/attachment/512695/import-error.log) into a private local working folder
3. Run the command below with those actual paths. The evaluator reads local files; it does not fetch or upload them

```sh
python3 scripts/evaluate.py \
  --public-csv /local/path/251202-import.csv \
  --public-log /local/path/import-error.log
```

Compare file hashes and the compact results in [evaluation](evaluation.md). The site's attachments or bug status may change. A mismatch is a reason to inspect the new evidence, not to assume our prior snapshot still applies.
