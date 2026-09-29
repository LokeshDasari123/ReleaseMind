import React, { useState } from 'react';
import { Brain, ChevronDown, ChevronUp } from 'lucide-react';

interface Props {
  reasoning: string;
}

const ModelReasoning: React.FC<Props> = ({ reasoning }) => {
  const [expanded, setExpanded] = useState(false);

  if (!reasoning) return null;

  return (
    <div className="model-reasoning-card card">
      <div 
        className="reasoning-header"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="reasoning-title">
          <Brain size={20} />
          <h3>Model Reasoning</h3>
        </div>
        <div className="reasoning-toggle">
          {expanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
        </div>
      </div>
      
      {expanded && (
        <div className="reasoning-content">
          <div className="reasoning-disclaimer">
            <em>Note: This section contains model inference and synthesis, not directly verified evidence.</em>
          </div>
          <div className="reasoning-text">
            {reasoning.split('\n').map((para, i) => (
              <p key={i}>{para}</p>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ModelReasoning;
