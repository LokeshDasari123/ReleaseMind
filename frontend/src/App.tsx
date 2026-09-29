import { useEffect, useRef, useState } from 'react';
import axios from 'axios';
import {
  Activity, AlertCircle, ArrowDown, ArrowUpRight, BookOpenText, Check, Database,
  FileUp, GitBranch, Loader2, LockKeyhole, Orbit, Sparkles,
} from 'lucide-react';
import { AssessmentResponse, MemoryStats, ServiceHealth } from './types';
import { getHealth, getMemoryStats, importDataset, submitChange } from './api';
import EvidencePanel from './components/EvidencePanel';
import RiskOverview from './components/RiskOverview';
import KeyRisks from './components/KeyRisks';
import Safeguards from './components/Safeguards';
import ModelReasoning from './components/ModelReasoning';
import './App.css';

const examples = [
  'Rotate signing keys while keeping existing access tokens valid during the rollout.',
  'Move request throttling from per-process memory to a Redis backed shared counter.',
  'Change the database connection pool defaults before the seasonal traffic peak.',
];

function errorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) return error.response?.data?.detail || error.message;
  return error instanceof Error ? error.message : 'Something went wrong.';
}

function App() {
  const [health, setHealth] = useState<ServiceHealth | null>(null);
  const [stats, setStats] = useState<MemoryStats | null>(null);
  const [description, setDescription] = useState('');
  const [context, setContext] = useState('');
  const [result, setResult] = useState<AssessmentResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [importBusy, setImportBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const refresh = async () => {
    const [healthResult, statsResult] = await Promise.allSettled([getHealth(), getMemoryStats()]);
    if (healthResult.status === 'fulfilled') setHealth(healthResult.value);
    if (statsResult.status === 'fulfilled') setStats(statsResult.value);
  };

  useEffect(() => { void refresh(); }, []);

  const analyze = async (event: React.FormEvent) => {
    event.preventDefault();
    if (description.trim().length < 8) return;
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      setResult(await submitChange(description.trim(), context.trim()));
    } catch (caught) {
      setError(errorMessage(caught));
    } finally {
      setBusy(false);
    }
  };

  const ingest = async (file?: File) => {
    if (!file) return;
    setImportBusy(true);
    setError(null);
    setNotice(null);
    try {
      const response = await importDataset(file);
      setNotice(`${response.imported} source records saved · ${response.skipped} skipped · ${response.memory_provider}`);
      await refresh();
    } catch (caught) {
      setError(errorMessage(caught));
    } finally {
      setImportBusy(false);
      if (fileRef.current) fileRef.current.value = '';
    }
  };

  const evidence = result?.retrieved_experiences || [];
  const cited = new Set(result?.memory_assessment.evidence_citations || []);

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#top" aria-label="ReleaseMind home">
          <span className="brand-mark"><Orbit size={20} strokeWidth={2.1} /></span>
          <span>release<span className="brand-light">mind</span></span>
          <span className="brand-version">FIELD NOTES / 01</span>
        </a>
        <div className="topbar-right">
          <span className={`service-pill ${health?.llm_configured ? 'online' : 'offline'}`}>
            <span className="status-dot" />{health?.llm_configured ? 'MODEL READY' : 'MODEL KEY NEEDED'}
          </span>
          <span className="memory-count"><Database size={15} /> {stats?.total_experiences ?? 0} incidents</span>
        </div>
      </header>

      <main id="top" className="page-wrap">
        <section className="hero-grid">
          <div className="hero-copy">
            <div className="eyebrow"><span className="eyebrow-line" /> RELEASE REVIEW / HISTORICAL MEMORY</div>
            <h1>Ship with<br /><span>institutional memory.</span></h1>
            <p className="hero-lede">Surface relevant incident knowledge while a change is still on the table. Inspect the source, weigh the context, and choose the safeguard.</p>
            <div className="scope-note"><LockKeyhole size={14} /><span>Decision support from historical reports. <strong>Not incident prediction.</strong></span></div>
          </div>
          <aside className="memory-card">
            <div className="memory-card-top"><span className="eyebrow">MEMORY BANK</span><Activity size={16} /></div>
            <div className="memory-number">{String(stats?.total_experiences ?? 0).padStart(2, '0')}</div>
            <div className="memory-label">source incidents available</div>
            <div className="memory-divider" />
            <p>{stats?.total_experiences ? `${Object.keys(stats.sources || {}).length} source collections · ${stats.provider}` : 'No incident reports loaded yet.'}</p>
            <button className="import-button" type="button" onClick={() => fileRef.current?.click()} disabled={importBusy}>
              {importBusy ? <Loader2 className="spin" size={15} /> : <FileUp size={15} />}
              {importBusy ? 'Importing records' : 'Import authorized data'}
              {!importBusy && <ArrowUpRight size={14} />}
            </button>
            <input ref={fileRef} className="visually-hidden" type="file" accept=".json,.csv,application/json,text/csv" onChange={(event) => void ingest(event.target.files?.[0])} />
            <small>JSON or CSV · only use records you are permitted to process</small>
          </aside>
        </section>

        <section className="workflow-strip" aria-label="ReleaseMind workflow">
          <div className="workflow-step active"><span>01</span><GitBranch size={15} /> Proposed change</div>
          <ArrowDown size={14} className="workflow-arrow" />
          <div className="workflow-step"><span>02</span><Database size={15} /> Incident memory</div>
          <ArrowDown size={14} className="workflow-arrow" />
          <div className="workflow-step"><span>03</span><Sparkles size={15} /> Evidence & safeguards</div>
          <div className="workflow-caption">TRACEABLE BY DESIGN</div>
        </section>

        <section className="workspace-grid">
          <div className="input-column">
            <div className="section-heading"><div><span className="section-index">01 / INPUT</span><h2>Describe the change</h2></div><span className="section-side-note">A release, migration, config change…</span></div>
            <form className="change-card" onSubmit={analyze}>
              <label htmlFor="change-description">WHAT IS CHANGING?</label>
              <textarea id="change-description" value={description} onChange={(event) => setDescription(event.target.value)} placeholder="e.g. Rotate signing keys while keeping existing tokens valid during the rollout…" maxLength={12000} />
              <label htmlFor="change-context">SYSTEM CONTEXT <span>OPTIONAL</span></label>
              <textarea id="change-context" className="context-area" value={context} onChange={(event) => setContext(event.target.value)} placeholder="Affected components, rollout plan, dependencies…" maxLength={4000} />
              <div className="change-card-footer"><span>{description.length.toLocaleString()} / 12,000</span><button type="submit" disabled={busy || description.trim().length < 8}>{busy ? <><Loader2 className="spin" size={17} /> Reviewing both conditions</> : <>Compare assessments <ArrowUpRight size={16} /></>}</button></div>
            </form>
            <div className="example-block"><div className="example-title">TRY A CHANGE SCENARIO <span>These are queries, not labeled outcomes.</span></div><div className="example-list">{examples.map((example) => <button type="button" key={example} onClick={() => setDescription(example)}>{example}<ArrowUpRight size={14} /></button>)}</div></div>
            {error && <div className="alert-box error-box"><AlertCircle size={17} /><span>{error}</span></div>}
            {notice && <div className="alert-box success-box"><Check size={17} /><span>{notice}</span></div>}
            {!health?.llm_configured && <div className="setup-callout"><AlertCircle size={17} /><p>To run assessments, add <code>OPENAI_API_KEY</code> to <code>backend/.env</code> and restart the backend.</p></div>}
            <div className="data-gate"><BookOpenText size={16} /><p><strong>Demo data source.</strong> This snapshot uses short Postmortem Index summaries under its declared GPL-3.0 corpus license; each record links to its original publisher. The VOID sample is not included.</p></div>
          </div>

          <div className="results-column">
            <div className="section-heading"><div><span className="section-index">02 / REVIEW</span><h2>Two lenses, one change</h2></div>{result && <span className="run-label">LIVE MODEL RUN · {result.metadata.llm_model}</span>}</div>
            {!result ? <div className="empty-state"><div className="empty-orbit"><Orbit size={24} /></div><h3>History, when you need it.</h3><p>Run an assessment to compare the change-only baseline with the same review grounded in retrieved incident records.</p><div className="empty-steps"><span>Change input</span><i /><span>Retrieve evidence</span><i /><span>Review safeguards</span></div></div> : <>
              <div className="conditions-grid">
                <AssessmentColumn title="Memory-free baseline" subtitle="Change + context only" icon="baseline" assessment={result.baseline_assessment} evidenceCount={0} cited={new Set()} />
                <AssessmentColumn title="Memory augmented" subtitle={`${result.metadata.evidence_count} retrieved report${result.metadata.evidence_count === 1 ? '' : 's'} · ${result.metadata.memory_provider}`} icon="memory" assessment={result.memory_assessment} evidenceCount={result.metadata.evidence_count} cited={cited} />
              </div>
              <div className="evidence-section"><div className="evidence-section-heading"><div><span className="section-index">03 / TRACE</span><h2>Historical evidence</h2></div><span>{evidence.length} retrieved</span></div><EvidencePanel experiences={evidence} citedIds={cited} /></div>
            </>}
          </div>
        </section>
      </main>

      <footer className="app-footer"><span>RELEASEMIND / ENGINEERING MEMORY</span><span>HISTORICAL REPORTS INFORM REVIEW · THEY DO NOT FORETELL OUTCOMES</span></footer>
    </div>
  );
}

function AssessmentColumn({ title, subtitle, icon, assessment, evidenceCount, cited }: {
  title: string; subtitle: string; icon: 'baseline' | 'memory'; assessment: AssessmentResponse['baseline_assessment']; evidenceCount: number; cited: Set<string>;
}) {
  return <article className={`assessment-card ${icon === 'memory' ? 'augmented-card' : ''}`}>
    <div className="assessment-card-heading"><span className={`condition-icon ${icon}`}><span>{icon === 'memory' ? <Orbit size={17} /> : 'LLM'}</span></span><div><h3>{title}</h3><p>{subtitle}</p></div></div>
    <RiskOverview assessment={assessment} />
    <div className="assessment-lists"><KeyRisks risks={assessment.key_risks} /><Safeguards safeguards={assessment.recommended_safeguards} /></div>
    <ModelReasoning reasoning={assessment.model_reasoning} />
    <div className="citation-line"><BookOpenText size={14} /><span>{cited.size} evidence citation{cited.size === 1 ? '' : 's'} used</span>{evidenceCount > 0 && <span className="retrieved-count">{evidenceCount} retrieved</span>}</div>
  </article>;
}

export default App;
