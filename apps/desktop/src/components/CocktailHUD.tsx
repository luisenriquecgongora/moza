import React from 'react';
import { Wine, Beer, AlertTriangle, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { MozaTelemetry } from '../hooks/useMozaTelemetry';

interface CocktailHUDProps {
  telemetry: MozaTelemetry;
}

export const CocktailHUD: React.FC<CocktailHUDProps> = ({ telemetry }) => {
  const trendIcon = {
    increasing: <TrendingUp size={16} color="var(--neon-green)" />,
    decreasing: <TrendingDown size={16} color="var(--neon-red)" />,
    stable: <Minus size={16} color="var(--text-muted)" />,
  }[telemetry.trend];

  return (
    <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 style={{ margin: 0, fontSize: '15px', fontWeight: 600, letterSpacing: '0.5px' }}>
          BAR & BEVERAGE INTELLIGENCE
        </h3>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', color: 'var(--text-muted)' }}>
          Trend: {trendIcon} <span style={{ textTransform: 'capitalize' }}>{telemetry.trend}</span>
        </div>
      </div>

      {/* Metrics Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' }}>
        {/* Cocktails & Wine */}
        <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '14px', borderRadius: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--neon-amber)' }}>
            <Wine size={18} />
            <span style={{ fontSize: '12px', fontWeight: 600 }}>STEMWARE</span>
          </div>
          <div style={{ fontSize: '26px', fontWeight: 700, marginTop: '8px', fontFamily: 'var(--font-mono)' }}>
            {telemetry.wine_glass_count}
          </div>
        </div>

        {/* Bottles */}
        <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '14px', borderRadius: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--neon-teal)' }}>
            <Beer size={18} />
            <span style={{ fontSize: '12px', fontWeight: 600 }}>BOTTLES</span>
          </div>
          <div style={{ fontSize: '26px', fontWeight: 700, marginTop: '8px', fontFamily: 'var(--font-mono)' }}>
            {telemetry.bottle_count}
          </div>
        </div>

        {/* Total Active Beverages */}
        <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '14px', borderRadius: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--neon-cyan)' }}>
            <Wine size={18} />
            <span style={{ fontSize: '12px', fontWeight: 600 }}>TOTAL DRINKS</span>
          </div>
          <div style={{ fontSize: '26px', fontWeight: 700, marginTop: '8px', fontFamily: 'var(--font-mono)' }}>
            {telemetry.total_beverages}
          </div>
        </div>
      </div>

      {/* Volumetric Fill-Level Gauge (Meniscus Model) */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '4px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: 'var(--text-muted)' }}>
          <span>Estimated Bar Consumption Rate</span>
          <span style={{ fontFamily: 'var(--font-mono)' }}>
            {telemetry.people_count > 0 ? (telemetry.total_beverages / telemetry.people_count).toFixed(2) : '0.00'} drinks/patron
          </span>
        </div>
        <div style={{ width: '100%', height: '8px', background: 'rgba(255,255,255,0.06)', borderRadius: '4px', overflow: 'hidden' }}>
          <div
            style={{
              width: `${Math.min(100, (telemetry.total_beverages / Math.max(1, telemetry.people_count * 2)) * 100)}%`,
              height: '100%',
              background: 'linear-gradient(90deg, var(--neon-teal), var(--neon-cyan))',
              transition: 'width 0.4s ease',
            }}
          />
        </div>
      </div>
    </div>
  );
};
