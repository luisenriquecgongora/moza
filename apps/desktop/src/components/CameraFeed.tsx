import React, { useState } from 'react';
import { Camera, AlertCircle, RefreshCw, ShieldCheck } from 'lucide-react';

interface CameraFeedProps {
  streamUrl?: string;
  isConnected: boolean;
}

export const CameraFeed: React.FC<CameraFeedProps> = ({
  streamUrl = 'http://127.0.0.1:8100/stream/video',
  isConnected,
}) => {
  const [loadError, setLoadError] = useState(false);
  const [key, setKey] = useState(0);

  const handleReload = () => {
    setLoadError(false);
    setKey((prev) => prev + 1);
  };

  return (
    <div
      style={{
        position: 'relative',
        width: '100%',
        height: '100%',
        background: '#07080a',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        overflow: 'hidden',
      }}
    >
      {/* Stream HUD Header */}
      <div
        style={{
          position: 'absolute',
          top: 16,
          left: 16,
          right: 16,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          zIndex: 5,
          pointerEvents: 'none',
        }}
      >
        <div
          className="glass-panel"
          style={{
            padding: '6px 12px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            pointerEvents: 'auto',
          }}
        >
          <Camera size={14} color="var(--neon-cyan)" />
          <span style={{ fontSize: '12px', fontWeight: 600, color: '#fff' }}>
            LOCAL CAMERA FEED
          </span>
          <span
            style={{
              fontSize: '10px',
              padding: '2px 6px',
              borderRadius: '4px',
              background: isConnected ? 'rgba(0, 242, 254, 0.2)' : 'rgba(255, 68, 68, 0.2)',
              color: isConnected ? 'var(--neon-cyan)' : 'var(--neon-red)',
              fontFamily: 'var(--font-mono)',
            }}
          >
            {isConnected ? 'LIVE 30 FPS' : 'OFFLINE'}
          </span>
        </div>

        <div
          className="glass-panel"
          style={{
            padding: '6px 12px',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '11px',
            color: 'var(--neon-green)',
            pointerEvents: 'auto',
          }}
        >
          <ShieldCheck size={14} />
          <span>100% OFFLINE LOCAL LOOPBACK (127.0.0.1)</span>
        </div>
      </div>

      {/* Main Video Element */}
      {isConnected && !loadError ? (
        <img
          key={key}
          src={streamUrl}
          alt="Moza Real-Time Computer Vision Stream"
          onError={() => setLoadError(true)}
          style={{
            maxWidth: '100%',
            maxHeight: '100%',
            objectFit: 'contain',
            boxShadow: '0 0 40px rgba(0, 242, 254, 0.1)',
          }}
        />
      ) : (
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '12px',
            color: 'var(--text-muted)',
            textAlign: 'center',
            padding: '24px',
          }}
        >
          <AlertCircle size={40} color="var(--neon-amber)" />
          <div style={{ fontSize: '15px', fontWeight: 600, color: '#fff' }}>
            Local Stream Inactive
          </div>
          <div style={{ fontSize: '12px', maxWidth: '340px' }}>
            Ensure the Moza Python daemon is running at{' '}
            <code style={{ color: 'var(--neon-cyan)' }}>http://127.0.0.1:8100</code>.
          </div>
          <button
            onClick={handleReload}
            className="glass-panel"
            style={{
              marginTop: '8px',
              padding: '8px 16px',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              color: '#fff',
              fontSize: '12px',
              cursor: 'pointer',
            }}
          >
            <RefreshCw size={14} />
            <span>Reconnect Stream</span>
          </button>
        </div>
      )}

      {/* Crosshair / Viewfinder Overlay */}
      <div
        style={{
          position: 'absolute',
          inset: '24px',
          border: '1px solid rgba(255, 255, 255, 0.05)',
          pointerEvents: 'none',
        }}
      >
        {/* Top-left corner */}
        <div style={{ position: 'absolute', top: -1, left: -1, width: 16, height: 16, borderTop: '2px solid var(--neon-cyan)', borderLeft: '2px solid var(--neon-cyan)' }} />
        {/* Top-right corner */}
        <div style={{ position: 'absolute', top: -1, right: -1, width: 16, height: 16, borderTop: '2px solid var(--neon-cyan)', borderRight: '2px solid var(--neon-cyan)' }} />
        {/* Bottom-left corner */}
        <div style={{ position: 'absolute', bottom: -1, left: -1, width: 16, height: 16, borderBottom: '2px solid var(--neon-cyan)', borderLeft: '2px solid var(--neon-cyan)' }} />
        {/* Bottom-right corner */}
        <div style={{ position: 'absolute', bottom: -1, right: -1, width: 16, height: 16, borderBottom: '2px solid var(--neon-cyan)', borderRight: '2px solid var(--neon-cyan)' }} />
      </div>
    </div>
  );
};
