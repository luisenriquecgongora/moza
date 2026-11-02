import React from 'react';
import { SpatialViewport } from './components/SpatialViewport';
import { CocktailHUD } from './components/CocktailHUD';
import { HazardAlertBanner } from './components/HazardAlertBanner';
import { useMozaTelemetry } from './hooks/useMozaTelemetry';
import { Eye, Users, Activity, Settings, Radio } from 'lucide-react';
import './styles/theme.css';

export const App: React.FC = () => {
  const { telemetry, isConnected } = useMozaTelemetry();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', width: '100vw', background: 'var(--bg-dark)' }}>
      {/* Top Header */}
      <header
        style={{
          height: '60px',
          borderBottom: '1px solid var(--border)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 24px',
          background: 'rgba(10, 11, 14, 0.9)',
          backdropFilter: 'blur(10px)',
          zIndex: 10,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ background: 'linear-gradient(135deg, var(--neon-cyan), var(--neon-teal))', padding: '8px', borderRadius: '8px', display: 'flex' }}>
            <Eye size={20} color="#000" />
          </div>
          <div>
            <div style={{ fontWeight: 700, fontSize: '16px', letterSpacing: '0.5px' }}>MOZA STUDIO</div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Autonomous Vision & Spatial Intelligence</div>
          </div>
        </div>

        {/* Status Indicators */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '18px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', fontFamily: 'var(--font-mono)' }}>
            <Radio size={16} color={isConnected ? 'var(--neon-green)' : 'var(--neon-red)'} />
            <span style={{ color: isConnected ? 'var(--neon-green)' : 'var(--neon-red)' }}>
              {isConnected ? 'PYTHON ENGINE ONLINE' : 'DISCONNECTED'}
            </span>
          </div>

          <button
            className="glass-panel"
            style={{
              padding: '6px 12px',
              color: '#fff',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '12px',
              cursor: 'pointer',
            }}
          >
            <Settings size={14} />
            <span>Settings</span>
          </button>
        </div>
      </header>

      {/* Main Workspace (Split View) */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Left: 3D Spatial Viewport */}
        <div style={{ flex: '1 1 65%', position: 'relative' }}>
          <SpatialViewport telemetry={telemetry} />
        </div>

        {/* Right: Telemetry & Alert Sidebar */}
        <div
          style={{
            flex: '1 1 35%',
            minWidth: '380px',
            maxWidth: '480px',
            borderLeft: '1px solid var(--border)',
            background: 'rgba(14, 16, 22, 0.85)',
            display: 'flex',
            flexDirection: 'column',
            gap: '16px',
            padding: '20px',
            overflowY: 'auto',
          }}
        >
          {/* Active Hazard Warning */}
          <HazardAlertBanner telemetry={telemetry} />

          {/* Crowd Occupancy Quick Card */}
          <div className="glass-panel" style={{ padding: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--neon-cyan)' }}>
                <Users size={18} />
                <span style={{ fontSize: '13px', fontWeight: 600 }}>CROWD OCCUPANCY</span>
              </div>
              <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Zone: Main Floor</span>
            </div>

            <div style={{ display: 'flex', alignItems: 'baseline', gap: '10px', marginTop: '12px' }}>
              <div style={{ fontSize: '42px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: '#fff' }}>
                {telemetry.people_count}
              </div>
              <div style={{ fontSize: '14px', color: 'var(--text-muted)' }}>
                patrons (5m avg: {telemetry.avg_count.toFixed(1)})
              </div>
            </div>
          </div>

          {/* Cocktail & Beverage Telemetry */}
          <CocktailHUD telemetry={telemetry} />

          {/* System Telemetry & Bobby CAD Homography Info */}
          <div className="glass-panel" style={{ padding: '16px', fontSize: '12px', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>Inference Pipeline</span>
              <span style={{ color: '#fff' }}>YOLOv11 + TransLab Glass</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>Acoustic Fracture Sensor</span>
              <span style={{ color: 'var(--neon-green)' }}>3-8kHz Band Active</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>3D Geometry Engine</span>
              <span style={{ color: 'var(--neon-amber)' }}>Synced with Bobby CAD</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>Privacy Guard</span>
              <span style={{ color: 'var(--neon-cyan)' }}>Zero-PII Face Obfuscation</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
