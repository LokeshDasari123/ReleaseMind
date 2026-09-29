import React from 'react';
import { AlertTriangle } from 'lucide-react';

interface Props {
  risks: string[];
}

const KeyRisks: React.FC<Props> = ({ risks }) => {
  if (!risks || risks.length === 0) return null;

  return (
    <div className="key-risks-card card">
      <h3><AlertTriangle size={20} className="icon-orange" /> Key Risks Identified</h3>
      <ol className="risks-list">
        {risks.map((risk, idx) => (
          <li key={idx}>
            <span className="risk-text">{risk}</span>
          </li>
        ))}
      </ol>
    </div>
  );
};

export default KeyRisks;
