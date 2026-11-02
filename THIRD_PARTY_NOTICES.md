# Third-Party Notices

Moza itself is licensed under the PolyForm Shield License 1.0.0 (see `LICENSE`).
It uses or downloads the following third-party components, each under its own license:

| Component | Used for | License |
|---|---|---|
| [YOLOX](https://github.com/Megvii-BaseDetection/YOLOX) ONNX model weights (`yolox_s.onnx`), Copyright (c) 2021-2022 Megvii Inc. | Multi-class object detection | [Apache-2.0](https://github.com/Megvii-BaseDetection/YOLOX/blob/main/LICENSE) |
| [ONNX Runtime](https://github.com/microsoft/onnxruntime) | Model inference | MIT |
| [MediaPipe](https://github.com/google-ai-edge/mediapipe) | Pose fallback detector | Apache-2.0 |
| [OpenCV](https://github.com/opencv/opencv) | Image processing | Apache-2.0 |

The YOLOX weights are not stored in this repository. They are downloaded from the
official YOLOX GitHub release on first use (into `models/`) or during the Docker build.
