import React from 'react';
import { ShieldCheck, CheckSquare } from 'lucide-react';

interface Props {
  safeguards: string[];
}

const Safeguards: React.FC<Props> = ({ safeguards }) => {
  if (!safeguards || safeguards.length === 0) return null;

  return (
    <div className="safeguards-card card">
      <h3><ShieldCheck size={20} className="icon-green" /> Recommended Safeguards</h3>
      <ul className="safeguards-list">
        {safeguards.map((safeguard, idx) => (
          <li key={idx}>
            <CheckSquare size={16} className="safeguard-icon" />
            <span className="safeguard-text">{safeguard}</span>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default Safeguards;
