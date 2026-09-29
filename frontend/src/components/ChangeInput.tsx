import React, { useState } from 'react';
import { Loader2, ChevronDown, ChevronUp } from 'lucide-react';

interface ChangeInputProps {
  onAssess: (description: string, context?: string) => void;
  loading: boolean;
}

const EXAMPLES = [
  'Upgrade authentication dependency from v2.x to v3.0 and modify session validation logic',
  'Add new database index on users table for email lookup optimization',
  'Migrate API rate limiting from in-memory to Redis-backed distributed rate limiter'
];

const ChangeInput: React.FC<ChangeInputProps> = ({ onAssess, loading }) => {
  const [description, setDescription] = useState('');
  const [context, setContext] = useState('');
  const [showContext, setShowContext] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (description.trim()) {
      onAssess(description, context);
    }
  };

  return (
    <div className="change-input-card card">
      <h2>Assess Proposed Change</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Describe your proposed change..."
            className="main-textarea"
            disabled={loading}
          />
        </div>
        
        <div className="context-toggle" onClick={() => setShowContext(!showContext)}>
          {showContext ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          <span>{showContext ? 'Hide Context' : 'Add Context (Optional)'}</span>
        </div>
        
        {showContext && (
          <div className="form-group">
            <textarea
              value={context}
              onChange={(e) => setContext(e.target.value)}
              placeholder="Add any additional context, PR descriptions, or related systems..."
              className="context-textarea"
              disabled={loading}
            />
          </div>
        )}

        <button 
          type="submit" 
          className="submit-btn"
          disabled={!description.trim() || loading}
        >
          {loading ? (
            <>
              <Loader2 className="spinner" size={20} />
              Assessing Risk...
            </>
          ) : (
            'Assess Risk'
          )}
        </button>
      </form>

      <div className="examples-section">
        <p className="examples-title">Or try an example:</p>
        <div className="examples-grid">
          {EXAMPLES.map((ex, idx) => (
            <div 
              key={idx} 
              className="example-card"
              onClick={() => setDescription(ex)}
            >
              {ex}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ChangeInput;
