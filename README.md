# Jira Import Doctor · experimental alpha

English | [简体中文](README.zh-CN.md)

**Source CSV + one import log → a reviewable diagnosis that separates file defects, possible parent cascades, and destination unknowns.**

The useful addition to CSV preflight is evidence across the file and failed attempt. It does not connect to Jira, upload files, edit the source, generate a repair patch, or rerun an import. No API key. Python 3.10+ standard library. Experimental, read-only diagnosis. Not validated as a production importer.

## Try the bundled example

With Git and Python 3.10+ available, clone the repository into a new directory:

```sh
git clone https://github.com/mozzie49/jira-import-doctor.git
cd jira-import-doctor
```

Run the synthetic example from the repository root:

```sh
python3 scripts/jira_import_doctor.py --csv examples/cascade-hypothesis/input.csv --log examples/cascade-hypothesis/import.log --context examples/cascade-hypothesis/context.json --out /tmp/jira-diagnosis-demo
```

Use a fresh output path if that folder exists. Read `/tmp/jira-diagnosis-demo/report.md` and `report.json`.

Expected result: four source records; three errors linked by explicit source IDs; two possible descendant cascades; an unrelated summary-only warning remains a candidate. The original CSV has no graph defect. The script never claims the assignee is the confirmed cause or that the import is now safe.

## Before → after: what the log changes

The source CSV is unchanged. These are **synthetic, shareable examples**, not customer outcomes or live imports.

| Evidence available | Cascade example result |
|---|---|
| [CSV only](examples/reports/cascade-hypothesis-before-csv-only.md) | Four records; no definite local graph defect; no evidence about the failed attempt |
| [CSV + log](examples/reports/cascade-hypothesis-after-with-log.md) | Source record 1 / ID `001` has a creation failure at log line 2. Records 2–3 have parent errors at log lines 3–4. Two cascade hypotheses are now evidence-linked |

**Next decision:** inspect the creation failure on record 1 before changing Parent values. The matching IDs are observed evidence; the explanation that this caused descendant errors remains a hypothesis. The unrelated warning at log line 5 matches only a summary and is left as a candidate.

The [second after-report](examples/reports/platform-ambiguous-after-with-log.md) demonstrates abstention: the log reports two creations despite an Epic Link warning. The warning's summary is a candidate, its key-shaped CustomField value is not a source key, and parent-link success is unverified. [CSV alone](examples/reports/platform-ambiguous-before-csv-only.md) cannot show any of that.

Rebuild these exact reports in a new folder:

```sh
python3 scripts/render_demos.py --out /tmp/jira-demo-reports
```

## Three honest demonstrations

All bundled CSVs/logs are synthetic, not customer case studies or real Jira runs.

1. `examples/graph-errors`: repeated import ID, missing parent, self-parent and cycle. Repeated Labels/Component columns and a multiline cell are preserved. This overlaps established preflight capability
2. `examples/cascade-hypothesis`: valid local graph plus an explicit ancestor creation failure and descendant parent errors. CSV-only checks cannot supply this attempt evidence
3. `examples/platform-ambiguous`: valid local graph, a known legacy-importer warning shape and reported creations. The report keeps the warning at summary-candidate level, recognizes a possible platform issue and does not declare that creation failed

The separate public-attachment validation is described in [evaluation](references/evaluation.md). Public observations are attributed in [sources](references/sources.md); the screenshots that could not be retrieved are not transcribed.

## Install the skill locally

Choose one destination. These layouts follow the official host documentation. They do not install the host itself. Run from the downloaded `jira-import-doctor` folder; the target must not already exist.

Claude Code project installation:

```sh
mkdir -p /path/to/project/.claude/skills
cp -R "$PWD" /path/to/project/.claude/skills/jira-import-doctor
```

Codex project installation:

```sh
mkdir -p /path/to/project/.agents/skills
cp -R "$PWD" /path/to/project/.agents/skills/jira-import-doctor
```

Open/restart a session in that project. Ask Claude Code `/jira-import-doctor` or Codex `$jira-import-doctor` to diagnose the CSV and log, supplying the actual importer route and intent. The CLI also works without an agent. The runtime agent may process content with its provider; only the Python helper is network-free.

No installer modifies home directories, settings, permissions, or credentials. Copy/run smoke testing is recorded below; real host discovery remains separately unverified where no clean host is available.

## Verify the pilot

```sh
python3 -m unittest discover -s tests -v
python3 scripts/validate_skill.py
python3 scripts/smoke_install.py
python3 scripts/evaluate.py
```

`validate_skill.py` checks required frontmatter, relative resources, and the reviewed runtime import allowlist. `smoke_install.py` copies the package into both host-shaped folders, validates the installed copy, and runs its CLI from outside the source tree under a socket/subprocess-denying guard. These checks do not exercise agent auto-discovery. [Hosted Linux CI](https://github.com/mozzie49/jira-import-doctor/actions/runs/38209314109) has passed the tests, validator, guarded install smokes, ablation and demo comparison on Python 3.10, 3.12 and 3.13.

`evaluate.py` runs a deterministic CSV-only ablation on the same bundled inputs and reports which findings require the log. It does not claim a measured win against a plain agent or Preflight Lab. [The evaluation note](references/evaluation.md) distinguishes tests passed, observed public evidence, and remaining release gates.

## Real inputs

Follow [SKILL.md](SKILL.md) and [the context contract](references/contract.md). Provide a source CSV, UTF-8 log from one attempt, and explicit context JSON. Unknowns are allowed and reduce certainty. Update files may legitimately reuse destination keys and have blank Summary cells. Missing/external parents and unsupported importer profiles stay uncertain.

Reports include best-effort secret/email redaction, not guaranteed anonymization. They can retain summaries, keys, IDs and unknown sensitive text. Inspect locally before sharing. Input files and logs are never uploaded by this package.

## Alpha limits and feedback

The reproducible package is suitable for supervised local feedback. Known limits are declared rather than treated as measured successes: actual host auto-discovery, a recurring-importer trial, and a competing-product comparison remain unverified. A small, non-controlled plain-agent comparison found no accuracy advantage; its initial counter-format miss and subsequent fix are documented in [evaluation](references/evaluation.md). No claim of superiority, guaranteed compatibility, import readiness, or live success is made.

A useful feedback report includes the importer/profile, intended operation, expected diagnostic decision, and a genuinely sanitized minimal CSV/log pair. Never include credentials or private customer files. [Fixture provenance](references/provenance.md) separates our synthetic demos from attributed public-source observations. No third-party attachment redistribution permission is assumed.

## License

[MIT](LICENSE) for original code, documentation and synthetic fixtures. Third-party Atlassian materials are excluded; see [provenance](references/provenance.md).
