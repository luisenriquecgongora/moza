# Moza 🍸

> *"At your service. Vision, cocktail perception & venue spatial intelligence for modern spaces."*  
> **Autonomous Edge Vision & Multimodal Venue Spatial Intelligence Engine**  
> **Python 3.12 / YOLOX (ONNX Runtime) / MediaPipe Edge Perception Daemon & Featherweight Client SDK**  
> Real-time crowd density, transparent glassware & cocktail tracking, broken glass hazard detection, and automated spatial telemetry for hospitality and commercial spaces.

[![License: PolyForm Shield 1.0.0](https://img.shields.io/badge/License-PolyForm_Shield_1.0.0-teal.svg)](LICENSE)
[![Edge Accelerated](https://img.shields.io/badge/Inference-ONNX_DirectML_CUDA-emerald.svg)](https://onnxruntime.ai)
[![Zero-PII Privacy](https://img.shields.io/badge/Privacy-Zero--PII_Invariants-blue.svg)](#-zero-pii-privacy-invariants)
[![Glassware Detection](https://img.shields.io/badge/Glassware-Refraction_Aware-purple.svg)](FUTURE_PLANS.md#initiative-1-transparent-glassware--cocktail-vessel-perception)
[![Architecture: SOLID & DRY](https://img.shields.io/badge/Architecture-SOLID_%26_DRY-blue.svg)](ARCHITECTURE.md)
[![Docker: Ready](https://img.shields.io/badge/Docker-Multi--Stage_Build-2496ED.svg?logo=docker&logoColor=white)](#-quickstart)
[![Research Roadmap](https://img.shields.io/badge/Research-10_SOTA_Initiatives-orange.svg)](FUTURE_PLANS.md)

---

## 🧠 The 10-Second Mental Model

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ 1. VIDEO & AUDIO INGEST ──> 🎥 USB / IP RTSP stream + 16kHz audio mic        │
│ 2. EDGE INFERENCE       ──> ⚡ YOLOX multi-class + TransLab glass rim +      │
│                               CSRNet crowd density + 3-8kHz shatter STFT     │
│ 3. SPATIAL REASONING    ──> 📐 Sliding-window trends, queue latency,         │
│                               and metric homography coordinates              │
│ 4. RULE ARBITRATION     ──> 🛡️ Priority rules with cooldowns & safety guards │
│ 5. TELEMETRY & EMISSION ──> 📡 Streams live JSON telemetry to Robot Host,    │
│                               Bobby CAD 3D maps, and cloud webhooks          │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 🏗️ Architecture & Component Topology

```mermaid
flowchart TD
    subgraph Ingest["Capture & Audio Ingress"]
        Cam["CameraManager (RTSP / USB 30 FPS)"]
        Mic["AudioCapture (dB Metering + 3-8kHz STFT)"]
    end

    subgraph Perception["Perception Engine"]
        YOLO["PersonDetector (People, Bottles, Devices, Hazards)"]
        Glass["GlasswareDetector (Clear Stemware, Meniscus)"]
        Shatter["ShatterDetector (Audio Shockwave + Visual Scatter)"]
        Crowd["CrowdDensityEngine (CSRNet Continuous Density)"]
    end

    subgraph Analytics["Spatial Intelligence & Rules"]
        DB["AnalyticsEngine (SQLite Time-Series metrics.db)"]
        Decide["DecisionEngine (Priority Queue & Cooldowns)"]
        Action["ActionExecutor (Alerts, Overlays, Webhooks)"]
    end

    subgraph Interface["Distribution & Clients"]
        Daemon["Moza Server (FastAPI / WebSocket / IPC)"]
        Client["MozaClient SDK (Featherweight, 0 CV Deps)"]
        RobotHost["Takient Robot Host"]
        Bobby["Bobby 3D Spatial CAD"]
    end

    Ingest --> Perception
    Perception --> Analytics
    Analytics --> Interface
    Daemon <--> Client
    Client --> RobotHost
    Daemon --> Bobby
```

---

## 🎯 Which Component Do I Need?

| If You Want To... | Target Component | Technology | Offline? |
| :--- | :--- | :--- | :---: |
| **Run vision intelligence on an edge device / camera** | `services/moza_server` | Python 3.12 / FastAPI / ONNX | **100% Offline** |
| **Integrate detection into Robot Host or custom app** | `clients/python/moza_client` | Python (Zero Heavy CV Deps) | **100% Offline** |
| **Run standalone CLI detection with OpenCV UI** | `src/moza/cli.py` | OpenCV / YOLO / MediaPipe | **100% Offline** |
| **Configure venue occupancy & hazard rules** | `configs/rules/crowd_density.json` | JSON SafeEval Rules | **100% Offline** |

---

## 🚀 Quickstart

### 1. Installation
```bash
# Clone the repository
git clone https://github.com/luisenriquecgongora/moza.git
cd moza

# Option A: One-Command Docker Deployment (Recommended for Edge Nodes)
docker compose up -d

# Option B: Local Python Installation
pip install -e ".[server,audio]"
```

### 2. Run the Detection CLI
```bash
# Launch interactive camera detection with multi-class models
python -m moza.cli --source 0 --resolution 1280x720 --confidence 0.35
```

### 3. Start the Moza Streaming Server
```bash
# Start edge daemon on port 8100
python -m services.moza_server.main --port 8100
```

### 4. Featherweight Client Usage (e.g. inside `robot_host`)
```python
from moza_client import MozaClient

# Connect to local or network Moza daemon (0 heavy CV dependencies required!)
client = MozaClient(host="127.0.0.1", port=8100)
client.connect()

# Fetch latest telemetry
telemetry = client.get_current_metrics()
print(f"People: {telemetry.people_count}, Cocktails: {telemetry.bottle_count}")
```

---

## 🛡️ Zero-PII Privacy Invariants

Moza is engineered ground-up for commercial hospitality and public venues:
1. **On-Edge Face Blurring**: Facial regions are blurred in memory before any frame buffer touches the disk or network.
2. **Zero Biometric Identity Storage**: Patrons are tracked via anonymous bounding-box geometry and centroid trajectories. No facial embeddings or biometric profiles are ever generated or persisted.
3. **Differential Privacy for Aggregate Trends**: Public crowd reports utilize Laplace noise perturbation to prevent individual patron tracking.

---

## 🔬 State-of-the-Art Research Track

Read our comprehensive 10 graduate-level research initiatives in [**FUTURE_PLANS.md**](FUTURE_PLANS.md), including:
- Transparent glassware boundary refraction modeling
- Liquid meniscus segmentation & cocktail fill-level estimation
- Dual-modal audio-visual broken glass fracture detection
- Continuous high-density crowd density regression (CSRNet)
- Multi-camera homography projection into Bobby 3D CAD space

---

## 📄 License
Moza is **source-available** under the [PolyForm Shield License 1.0.0](LICENSE). It is not open source.

- ✅ **Free for any business to use**, including commercially, to run its own operations: bars, clubs, venues, shops, companies.
- ✅ You may read, modify and share the code, as long as you keep the license and the `Required Notice` line.
- ❌ You may **not** use Moza, or any copy or modified version of it, to provide a product or service that **competes** with Moza or with any product the licensor provides using it.

For commercial, partner, or OEM licensing, contact **luisenriquecgongora@gmail.com**.

Copyright (c) 2026 Luis Enrique. All rights not expressly granted are reserved.
