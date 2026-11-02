import React, { useState, useEffect } from 'react';
import { X, Sliders, Shield, Camera, Check, Server } from 'lucide-react';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({ isOpen, onClose }) => {
  const [confidence, setConfidence] = useState<number>(0.35);
  const [anonymizeFaces, setAnonymizeFaces] = useState<boolean>(true);
  const [source, setSource] = useState<string>('0');
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [saveSuccess, setSaveSuccess] = useState<boolean>(false);

  useEffect(() => {
    if (!isOpen) return;

    fetch('http://127.0.0.1:8100/config')
      .then((res) => res.json())
      .then((data) => {
        if (data.confidence !== undefined) setConfidence(data.confidence);
        if (data.anonymize_faces !== undefined) setAnonymizeFaces(data.anonymize_faces);
        if (data.source !== undefined) setSource(String(data.source));
      })
      .catch((err) => {
        console.warn('Could not load remote config:', err);
      });
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const res = await fetch('http://127.0.0.1:8100/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          confidence: Number(confidence),
          anonymize_faces: anonymizeFaces,
          source: source,
        }),
      });
      if (res.ok) {
        setSaveSuccess(true);
        setTimeout(() => setSaveSuccess(false), 2000);
      }
    } catch (err) {
      console.error('Failed to save settings:', err);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 100,
        backgroundColor: 'rgba(0, 0, 0, 0.75)',
        backdropFilter: 'blur(8px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
      onClick={onClose}
    >
      <div
        className="glass-panel"
        style={{
          width: '90%',
          maxWidth: '520px',
          background: 'rgba(14, 16, 22, 0.95)',
          border: '1px solid var(--border)',
          borderRadius: '12px',
          padding: '24px',
          display: 'flex',
          flexDirection: 'column',
          gap: '20px',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Sliders size={20} color="var(--neon-cyan)" />
            <h2 style={{ fontSize: '18px', fontWeight: 700, margin: 0, color: '#fff' }}>
              Engine Settings
            </h2>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text-muted)',
              cursor: 'pointer',
              display: 'flex',
              padding: '4px',
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Local Offline Banner */}
        <div
          style={{
            background: 'rgba(0, 242, 254, 0.08)',
            border: '1px solid rgba(0, 242, 254, 0.25)',
            borderRadius: '8px',
            padding: '10px 14px',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            fontSize: '12px',
            color: 'var(--neon-cyan)',
          }}
        >
          <Server size={16} />
          <div>
            <strong>100% Local Loopback Mode:</strong> All vision processing runs on your local
            machine at <code>127.0.0.1:8100</code>. No remote servers or cloud accounts required.
          </div>
        </div>

        {/* Setting 1: Detection Confidence */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
            <span style={{ fontWeight: 600 }}>YOLO Detection Threshold</span>
            <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--neon-cyan)' }}>
              {Math.round(confidence * 100)}%
            </span>
          </div>
          <input
            type="range"
            min="0.10"
            max="0.95"
            step="0.05"
            value={confidence}
            onChange={(e) => setConfidence(parseFloat(e.target.value))}
            style={{ width: '100%', accentColor: 'var(--neon-cyan)' }}
          />
          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
            Higher values reduce false positives; lower values improve recall in low-light venues.
          </span>
        </div>

        {/* Setting 2: Privacy Anonymization */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Shield size={18} color="var(--neon-green)" />
            <div>
              <div style={{ fontSize: '13px', fontWeight: 600 }}>Zero-PII Face Blurring</div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                Hardware Gaussian blur on patron faces prior to rendering
              </div>
            </div>
          </div>
          <input
            type="checkbox"
            checked={anonymizeFaces}
            onChange={(e) => setAnonymizeFaces(e.target.checked)}
            style={{ width: '18px', height: '18px', accentColor: 'var(--neon-green)' }}
          />
        </div>

        {/* Setting 3: Camera Device Source */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', fontWeight: 600 }}>
            <Camera size={16} color="var(--neon-amber)" />
            <span>Vision Input Source</span>
          </div>
          <input
            type="text"
            value={source}
            onChange={(e) => setSource(e.target.value)}
            placeholder="0 or rtsp://camera-ip/live"
            style={{
              padding: '8px 12px',
              borderRadius: '6px',
              border: '1px solid var(--border)',
              background: 'rgba(0, 0, 0, 0.4)',
              color: '#fff',
              fontSize: '13px',
              fontFamily: 'var(--font-mono)',
            }}
          />
          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
            Enter USB index (e.g. <code>0</code> or <code>1</code>) or an RTSP/HTTP camera feed URL.
          </span>
        </div>

        {/* Footer Actions */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px' }}>
          <button
            onClick={onClose}
            className="glass-panel"
            style={{ padding: '8px 16px', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '13px' }}
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving}
            style={{
              padding: '8px 20px',
              borderRadius: '8px',
              border: 'none',
              background: saveSuccess ? 'var(--neon-green)' : 'var(--neon-cyan)',
              color: '#000',
              fontWeight: 700,
              cursor: isSaving ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '13px',
              transition: 'background 0.2s ease',
            }}
          >
            {saveSuccess ? (
              <>
                <Check size={16} />
                <span>Saved!</span>
              </>
            ) : (
              <span>{isSaving ? 'Applying...' : 'Apply Changes'}</span>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
