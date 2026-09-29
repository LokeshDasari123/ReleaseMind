# Local demo data manifest

- Dataset: Postmortem Index (icco/postmortems / postmortems.app)
- Dataset page: https://postmortems.app/about
- Machine-readable records: https://postmortems.app/output/
- Code/data repository: https://github.com/icco/postmortems
- Declared corpus license: GPL-3.0, as shown by the publisher's About page and GitHub repository.
- Retrieved: 2026-09-29
- Snapshot: 195 importable records from 242 incident entries (records without required title, short summary, or source URL were excluded).
- Stored source snapshot: data/postmortem-index-demo.json (included with GPL-3.0 notice)
- SHA-256: a4c3c265f546e758467075aaec890ea4275a06fbd21df2b66c0aa1526389724c
- Import: 195 records into the persistent SQLite memory database; source URLs retained per record.

The imported text uses the index's short Summary field only. It does not include full linked postmortem bodies. The index's stated GPL-3.0 license applies to the index corpus; each linked report remains governed by its own publisher's terms. Original source URLs remain attached to evidence in ReleaseMind. The dataset contains incident summaries and metadata, not a verified change-to-deployment-to-incident chain. Root cause and remediation fields are left empty unless explicitly structured in the source data; the model may summarize facts present in the short incident synopsis and must cite its source record.

Credit: “Postmortem Index, maintained by icco and contributors, GPL-3.0; individual incident reports remain the property of their original publishers.”