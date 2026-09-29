import { AlertCircle, ArrowUpRight, BookOpenText, Link2 } from 'lucide-react';
import { HistoricalExperience } from '../types';

interface Props { experiences: HistoricalExperience[]; citedIds: Set<string>; }

export default function EvidencePanel({ experiences, citedIds }: Props) {
  if (!experiences.length) return <div className="evidence-empty"><AlertCircle size={17} /><p>No incident records were retrieved for this query. The augmented assessment should rely on general reasoning and state this evidence gap.</p></div>;
  return <div className="evidence-list">
    {experiences.map((item, index) => {
      const cited = citedIds.has(item.id);
      return <article className={`evidence-card ${cited ? 'is-cited' : ''}`} key={item.id}>
        <div className="evidence-card-top"><span className="evidence-rank">0{index + 1}</span><span className="evidence-kind">HISTORICAL REPORT</span><code className="evidence-id">{item.id}</code>{cited && <span className="cited-badge"><BookOpenText size={12} /> CITED IN REVIEW</span>}</div>
        <h3>{item.title}</h3>
        <div className="evidence-meta"><span>{item.source}</span>{item.date && <span>{item.date}</span>}{item.severity && <span className="severity-chip">{item.severity}</span>}</div>
        <p className="evidence-description">{item.description}</p>
        {item.triggering_change && <div className="evidence-fact"><strong>REPORTED CHANGE</strong><p>{item.triggering_change}</p></div>}
        {item.root_cause && <div className="evidence-fact"><strong>REPORTED CAUSE</strong><p>{item.root_cause}</p></div>}
        {item.remediation && <div className="evidence-fact remediation-fact"><strong>REPORTED RESPONSE</strong><p>{item.remediation}</p></div>}
        {item.services_affected.length > 0 && <div className="component-row"><span>COMPONENTS</span>{item.services_affected.map((service) => <span className="component-chip" key={service}>{service}</span>)}</div>}
        <a className="source-anchor" href={item.source_url} target="_blank" rel="noreferrer"><Link2 size={14} /> Open original source <ArrowUpRight size={13} /></a>
      </article>;
    })}
  </div>;
}
