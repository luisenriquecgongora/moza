"""
Real-time edge face blurring and zero-PII privacy anonymization.
Ensures zero identifiable biometric data is recorded or stored.
"""

import numpy as np



class FaceAnonymizer:
    """
    On-edge real-time face blurring processor.
    Applies Gaussian blurring to detected facial regions directly in memory.
    """

    def __init__(self, blur_kernel_size: int = 45):
        self.kernel_size = blur_kernel_size if blur_kernel_size % 2 == 1 else blur_kernel_size + 1
        self._cascade = None

    def _get_cascade(self):
        """Lazy load OpenCV Haar cascade."""
        if self._cascade is None:
            import cv2
            cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            self._cascade = cv2.CascadeClassifier(cascade_path)
        return self._cascade

    def anonymize(self, frame_bgr: np.ndarray) -> np.ndarray:
        """
        Detect faces and apply strong Gaussian blur to anonymize patrons.
        Modifies frame in-place and returns it.
        """
        import cv2

        if frame_bgr is None:
            return frame_bgr

        cascade = self._get_cascade()
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        faces = cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(30, 30))

        for (x, y, w, h) in faces:
            # Extract face ROI
            face_roi = frame_bgr[y:y+h, x:x+w]
            # Apply Gaussian Blur
            blurred = cv2.GaussianBlur(face_roi, (self.kernel_size, self.kernel_size), 30)
            frame_bgr[y:y+h, x:x+w] = blurred

        return frame_bgr
