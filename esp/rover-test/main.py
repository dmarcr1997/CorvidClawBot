import requests
import cv2
import numpy as np
import time
import threading
import queue

ESP32_URL = "http://192.168.1.99"


def gaussian_pyramid(img, levels):
    pyramid = [img]
    for _ in range(levels - 1):
        img = cv2.pyrDown(img)
        pyramid.append(img)
    return pyramid

def optic_flow_lk(img_a, img_b, k_size, sigma):
    kernel = cv2.getGaussianKernel(k_size, sigma)
    kernel = kernel @ kernel.T
    Ix = cv2.filter2D(img_a, -1, np.array([[-1, 0, 1]]))
    Iy = cv2.filter2D(img_a, -1, np.array([[-1], [0], [1]]))
    It = img_b - img_a
    Ixx = cv2.filter2D(Ix ** 2, -1, kernel)
    Iyy = cv2.filter2D(Iy ** 2, -1, kernel)
    Ixy = cv2.filter2D(Ix * Iy, -1, kernel)
    Ixt = cv2.filter2D(Ix * It, -1, kernel)
    Iyt = cv2.filter2D(Iy * It, -1, kernel)
    det = Ixx * Iyy - Ixy ** 2
    det = np.where(np.abs(det) < 1e-6, 1e-6, det)
    U = -(Iyy * Ixt - Ixy * Iyt) / det
    V = -(Ixx * Iyt - Ixy * Ixt) / det
    return U, V

def warp(img, U, V,
         interpolation=cv2.INTER_CUBIC,
         border_mode=cv2.BORDER_REFLECT101):
    h, w = img.shape[:2]
    x, y = np.meshgrid(np.arange(w), np.arange(h))
    map_x = (x + U).astype(np.float32)
    map_y = (y + V).astype(np.float32)
    return cv2.remap(img, map_x, map_y, interpolation, borderMode=border_mode)

def hierarchical_lk(img_a, img_b, levels=2, k_size=7, sigma=1.5,
                    interpolation=cv2.INTER_CUBIC,
                    border_mode=cv2.BORDER_REFLECT101):
    # run HLK on raw low-res frames — upscale happens after
    a = cv2.cvtColor(img_a, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
    b = cv2.cvtColor(img_b, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0

    pyr_a = gaussian_pyramid(a, levels)
    pyr_b = gaussian_pyramid(b, levels)

    U = np.zeros_like(pyr_a[levels - 1])
    V = np.zeros_like(pyr_a[levels - 1])

    for i in range(levels - 1, -1, -1):
        A = pyr_a[i]
        B = pyr_b[i]
        B_warped = warp(B, U, V, interpolation, border_mode)
        dU, dV = optic_flow_lk(A, B_warped, k_size, sigma)
        U = U + dU
        V = V + dV
        if i > 0:
            U = cv2.pyrUp(U) * 2.0
            V = cv2.pyrUp(V) * 2.0
            h, w = pyr_a[i - 1].shape[:2]
            U = U[:h, :w]
            V = V[:h, :w]
    return U, V

def interpolate_frames(frame_a, frame_b, U, V, steps=5,
                       output_size=(640, 480)):
    """Interpolate on low-res frames then upscale results."""
    frames = []
    for t in np.linspace(0, 1, steps + 2)[1:-1]:
        I1_t = warp(frame_a.astype(np.float32), -t * U, -t * V)
        I2_t = warp(frame_b.astype(np.float32), (1 - t) * U, (1 - t) * V)
        blended = ((1 - t) * I1_t + t * I2_t).clip(0, 255).astype(np.uint8)
        # upscale after interpolation not before
        upscaled = cv2.resize(blended, output_size, interpolation=cv2.INTER_CUBIC)
        frames.append(upscaled)
    return frames

class FrameCapture:
    """Captures frames in a background thread so HLK never waits on network."""

    def __init__(self, capture_fps=10):
        self.capture_delay = 1.0 / capture_fps
        self.frame_queue = queue.Queue(maxsize=2)
        self.stopped = False
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()

    def _worker(self):
        while not self.stopped:
            try:
                response = requests.get(f"{ESP32_URL}/capture", timeout=2)
                img_array = np.frombuffer(response.content, dtype=np.uint8)
                frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                if frame is not None:
                    # drop oldest if full — always keep latest
                    if self.frame_queue.full():
                        try:
                            self.frame_queue.get_nowait()
                        except queue.Empty:
                            pass
                    self.frame_queue.put(frame)
            except Exception as e:
                print(f"Capture error: {e}")
            time.sleep(self.capture_delay)

    def get(self, timeout=5.0):
        try:
            return self.frame_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def stop(self):
        self.stopped = True

def interpolated_stream(capture_fps=10, interp_steps=5,
                        lk_levels=2, k_size=7, sigma=1.5,
                        output_size=(640, 480)):
    """
    - Capture threaded at low fps on raw 320x240
    - HLK on low-res frames (fast)
    - Upscale interpolated frames to output_size
    capture_fps=10 + interp_steps=5 → ~60fps effective output
    """
    capturer = FrameCapture(capture_fps=capture_fps)

    # warm up — retry until we get two valid frames
    prev_frame = None
    while prev_frame is None:
        prev_frame = capturer.get()

    curr_frame = None
    while curr_frame is None:
        curr_frame = capturer.get()

    try:
        while True:
            t0 = time.time()

            U, V = hierarchical_lk(
                prev_frame, curr_frame,
                levels=lk_levels,
                k_size=k_size,
                sigma=sigma
            )

            print(f"HLK took: {(time.time()-t0)*1000:.1f}ms")

            middle_frames = interpolate_frames(
                prev_frame, curr_frame, U, V,
                steps=interp_steps,
                output_size=output_size
            )
            for f in middle_frames:
                yield f

            yield cv2.resize(curr_frame, output_size, interpolation=cv2.INTER_CUBIC)

            prev_frame = curr_frame

            # retry until valid frame — handles WiFi hiccups and slow ESP32 responses
            next_frame = None
            while next_frame is None:
                next_frame = capturer.get()
            curr_frame = next_frame

    except KeyboardInterrupt:
        pass
    finally:
        capturer.stop()


if __name__ == "__main__":
    for frame in interpolated_stream(
        capture_fps=20,
        interp_steps=5,
        lk_levels=3,
        k_size=11,
        sigma=2.5,
        output_size=(640, 480)
    ):
        cv2.imshow("ClawBot", frame)
        if cv2.waitKey(1) == ord('q'):
            break
    cv2.destroyAllWindows()