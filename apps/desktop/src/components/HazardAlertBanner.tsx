import React from 'react';
import { AlertOctagon, CheckCircle2 } from 'lucide-react';
import { MozaTelemetry } from '../hooks/useMozaTelemetry';

interface HazardAlertBannerProps {
  telemetry: MozaTelemetry;
}

export const HazardAlertBanner: React.FC<HazardAlertBannerProps> = ({ telemetry }) => {
  const hasBrokenGlass = telemetry.broken_glass;
  const hasKnife = telemetry.knife_count > 0;
  const hasAnyHazard = hasBrokenGlass || hasKnife || telemetry.total_hazards > 0;

  if (!hasAnyHazard) {
    return (
      <div
        className="glass-panel"
        style={{
          padding: '12px 18px',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          color: 'var(--neon-green)',
          fontSize: '13px',
        }}
      >
        <CheckCircle2 size={18} />
        <span>VENUE STATUS NOMINAL — NO ACTIVE SAFETY HAZARDS</span>
      </div>
    );
  }

  return (
    <div
      className="glass-panel pulse-strobe"
      style={{
        padding: '16px 20px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        background: 'rgba(255, 8, 68, 0.15)',
        borderColor: 'var(--neon-red)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        <AlertOctagon size={28} color="var(--neon-red)" />
        <div>
          <div style={{ fontWeight: 700, fontSize: '15px', color: 'var(--neon-red)', letterSpacing: '0.5px' }}>
            {hasBrokenGlass ? '🚨 BROKEN GLASS SHATTER DETECTED' : '⚠️ ACTIVE VENUE HAZARD ALERT'}
          </div>
          <div style={{ fontSize: '13px', color: '#fca5a5', marginTop: '2px' }}>
            {hasBrokenGlass
              ? 'High-frequency acoustic fracture impulse (3-8kHz) + specular optical dispersion verified.'
              : `${telemetry.total_hazards} security hazard(s) flagged by vision pipeline.`}
          </div>
        </div>
      </div>

      <button
        style={{
          background: 'var(--neon-red)',
          color: '#fff',
          border: 'none',
          padding: '8px 16px',
          borderRadius: '6px',
          fontWeight: 600,
          cursor: 'pointer',
          fontSize: '13px',
        }}
        onClick={() => alert('Staff notification dispatched via Moza DecisionEngine.')}
      >
        DISPATCH STAFF
      </button>
    </div>
  );
};
