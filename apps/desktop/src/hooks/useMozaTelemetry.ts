import { useState, useEffect } from 'react';

export interface MozaTelemetry {
  status: string;
  people_count: number;
  bottle_count: number;
  wine_glass_count: number;
  total_beverages: number;
  knife_count: number;
  total_hazards: number;
  broken_glass: boolean;
  trend: 'increasing' | 'decreasing' | 'stable';
  avg_count: number;
  timestamp: number;
}

const DEFAULT_TELEMETRY: MozaTelemetry = {
  status: 'connecting',
  people_count: 0,
  bottle_count: 0,
  wine_glass_count: 0,
  total_beverages: 0,
  knife_count: 0,
  total_hazards: 0,
  broken_glass: false,
  trend: 'stable',
  avg_count: 0,
  timestamp: Date.now() / 1000,
};

export function useMozaTelemetry(wsUrl: string = 'ws://127.0.0.1:8100/ws/telemetry') {
  const [telemetry, setTelemetry] = useState<MozaTelemetry>(DEFAULT_TELEMETRY);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    let ws: WebSocket | null = null;
    let reconnectTimeout: any = null;

    function connect() {
      try {
        ws = new WebSocket(wsUrl);

        ws.onopen = () => {
          setIsConnected(true);
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data && typeof data === 'object') {
              setTelemetry(data);
            }
          } catch {
            // Ignore non-json pings
          }
        };

        ws.onclose = () => {
          setIsConnected(false);
          setTelemetry((prev) => ({ ...prev, status: 'offline' }));
          reconnectTimeout = setTimeout(connect, 2000);
        };

        ws.onerror = () => {
          ws?.close();
        };
      } catch {
        reconnectTimeout = setTimeout(connect, 3000);
      }
    }

    connect();

    return () => {
      if (ws) ws.close();
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
    };
  }, [wsUrl]);

  return { telemetry, isConnected };
}
