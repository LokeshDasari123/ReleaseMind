# ReleaseMind incident data

## Loaded video-demo snapshot

The local SQLite memory currently contains 195 source-linked short summaries from the [Postmortem Index](https://postmortems.app/about), a public machine-readable corpus whose publisher declares GPL-3.0. The page currently lists 242 postmortems; only rows with a title, short summary, and original source URL were loaded. Snapshot date, import details, and SHA-256 are recorded in [SOURCE-MANIFEST.md](SOURCE-MANIFEST.md).

The import uses each entry's short `Summary` field, company, category, product, date where available, and original source URL. It does not copy full linked report bodies. The index license does not relicense the original reports; each upstream publisher's terms still apply. Evidence cards link directly to those sources. Root-cause and remediation fields are left blank unless the imported record explicitly provides structured values; ReleaseMind may reason from the short summary, but must cite the source and distinguish inference from reported fact.

**Credit:** Postmortem Index (`icco/postmortems` and postmortems.app contributors), GPL-3.0. Individual linked postmortem reports remain copyright of their original publishers. The sample supports historical retrieval only; it does not establish general deployment-to-incident causality.

The demo snapshot is local and git-ignored. Download it through the source links below or import any compatible authorized JSON/CSV via the UI/API:

- <https://postmortems.app/output/>
- <https://github.com/icco/postmortems>

## VOID and AWS sources

The TU Delft 348-report VOID sample remains excluded until its exact file license and source-report rights are confirmed. See [research/licenses.md](../research/licenses.md). The [AWS Post-Event Summaries page](https://aws.amazon.com/premiumsupport/technology/pes/) is an official index of AWS summaries, not a bulk incident dataset; it can be cited as a source but AWS report terms still apply.

## Import schema

For other JSON/CSV data, the importer requires a title, narrative/summary, and HTTP(S) source URL. It preserves optional source-provided date, service, category, cause, remediation, and severity fields. Missing values remain empty; the importer does not infer deployment IDs or causal relationships. See `data/README.md` history in the docs or the field aliases documented in the root README.