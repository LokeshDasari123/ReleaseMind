import React from 'react';
import { RiskAssessment } from '../types';
import { AlertTriangle, AlertCircle, Info, CheckCircle } from 'lucide-react';

interface Props {
  assessment: RiskAssessment;
}

const getRiskColors = (level: string) => {
  switch (level) {
    case 'LOW': return { bg: 'var(--risk-low-bg)', color: 'var(--risk-low-text)', icon: CheckCircle };
    case 'MEDIUM': return { bg: 'var(--risk-medium-bg)', color: 'var(--risk-medium-text)', icon: Info };
    case 'HIGH': return { bg: 'var(--risk-high-bg)', color: 'var(--risk-high-text)', icon: AlertTriangle };
    case 'CRITICAL': return { bg: 'var(--risk-critical-bg)', color: 'var(--risk-critical-text)', icon: AlertCircle };
    default: return { bg: '#e5e7eb', color: '#374151', icon: Info };
  }
};

const RiskOverview: React.FC<Props> = ({ assessment }) => {
  const colors = getRiskColors(assessment.risk_level);
  const Icon = colors.icon;

  return (
    <div className="risk-overview-card card">
      <div className="risk-header">
        <div className="risk-badge" style={{ backgroundColor: colors.bg, color: colors.color }}>
          <Icon size={24} />
          <span>{assessment.risk_level} RISK</span>
        </div>
        <div className="risk-score-container">
          <div className="risk-score-label">Risk Score: {assessment.risk_score}/100</div>
          <div className="progress-bar-bg">
            <div 
              className="progress-bar-fill" 
              style={{ 
                width: `${assessment.risk_score}%`,
                backgroundColor: colors.color
              }} 
            />
          </div>
        </div>
      </div>
      
      <div className="risk-summary">
        <h3>Summary</h3>
        <p>{assessment.summary}</p>
      </div>

      {assessment.confidence_notes && (
        <div className="confidence-notes">
          <strong>Confidence Notes:</strong> {assessment.confidence_notes}
        </div>
      )}
    </div>
  );
};

export default RiskOverview;
