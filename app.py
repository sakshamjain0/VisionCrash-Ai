import datetime
import functools
import os
import tempfile

import cv2
import gradio as gr
import numpy as np
import tensorflow as tf
from object_detection.utils import label_map_util

import email_alert
import sms_alert

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PATH_TO_SAVED_MODEL = os.path.join(_BASE_DIR, "inference_graph", "saved_model")
PATH_TO_LABEL_MAP = os.path.join(_BASE_DIR, "label_map.pbtxt")
SAMPLE_VIDEO = os.path.join(_BASE_DIR, "test_videos", "test (10).mp4")


@functools.lru_cache(maxsize=1)
def load_detector():
    """Load and cache the TensorFlow SavedModel and label map."""
    detect_fn = tf.saved_model.load(PATH_TO_SAVED_MODEL)
    category_index = label_map_util.create_category_index_from_labelmap(
        PATH_TO_LABEL_MAP,
        use_display_name=True,
    )
    return detect_fn, category_index


def _trigger_alerts(source_name):
    """Send configured email and SMS alerts, returning a human-readable summary."""
    results = []
    try:
        em = email_alert.Email(source_name)
        em.run_mail()
        results.append("Email: Sent")
    except Exception as exc:
        results.append(f"Email: Failed ({exc})")

    try:
        sm = sms_alert.Sms(source_name)
        sms_ok, sms_msg = sm.run_sms()
        results.append(f"SMS: {'Sent' if sms_ok else 'Skipped/Failed'} ({sms_msg})")
    except Exception as exc:
        results.append(f"SMS: Failed ({exc})")

    return "\n".join(results)


def analyze_video(video_path, score_thresh, send_alerts):
    """Run frame-by-frame crash detection on an uploaded video."""
    if not video_path:
        return None, None, "Please upload a video file first."

    detect_fn, category_index = load_detector()

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None, None, "Unable to open the uploaded video."

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 640
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480
    fps = cap.get(cv2.CAP_PROP_FPS) or 15.0
    if fps <= 0 or fps > 60:
        fps = 15.0

    os.makedirs(os.path.join(_BASE_DIR, "outputs", "frame_img"), exist_ok=True)
    out_fd, out_video_path = tempfile.mkstemp(suffix=".mp4")
    os.close(out_fd)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(out_video_path, fourcc, fps, (width, height))

    detection_hits = 0
    max_score = 0.0
    captured_frame_rgb = None
    captured_frame_path = None
    total_frames = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            total_frames += 1
            image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            input_tensor = tf.expand_dims(tf.convert_to_tensor(image_rgb), axis=0)
            detections = detect_fn(input_tensor)

            score = float(detections["detection_scores"][0, 0].numpy())
            bbox = detections["detection_boxes"][0, 0].numpy()
            label_id = int(detections["detection_classes"][0, 0].numpy())
            label_name = category_index.get(label_id, {}).get("name", "Crash")

            if score > max_score:
                max_score = score

            if score >= score_thresh:
                detection_hits += 1
                ymin, xmin, ymax, xmax = (
                    int(bbox[0] * height),
                    int(bbox[1] * width),
                    int(bbox[2] * height),
                    int(bbox[3] * width),
                )
                cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (0, 0, 255), 2)
                cv2.putText(
                    frame,
                    f"{label_name}: {int(score * 100)}%",
                    (xmin, max(25, ymin - 8)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (255, 255, 255),
                    2,
                )

                if captured_frame_rgb is None:
                    captured_frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
                    captured_frame_path = os.path.join(
                        _BASE_DIR, "outputs", "frame_img", f"vcd_frame{ts}.jpg"
                    )
                    cv2.imwrite(captured_frame_path, frame)

            writer.write(frame)
    finally:
        cap.release()
        writer.release()

    if detection_hits > 0:
        status_lines = [
            f"CRASH DETECTED in {detection_hits} / {total_frames} frames (max confidence: {max_score:.1%})."
        ]
        if send_alerts:
            status_lines.append(_trigger_alerts(os.path.basename(video_path)))
        else:
            status_lines.append("Alerts not sent (enable 'Send Email/SMS Alerts' if configured).")
    else:
        status_lines = [
            f"No crash detected across {total_frames} frames above {score_thresh:.0%} threshold (max confidence: {max_score:.1%})."
        ]

    return out_video_path, captured_frame_rgb, "\n".join(status_lines)


examples = [[SAMPLE_VIDEO, 0.90, False]] if os.path.exists(SAMPLE_VIDEO) else None

with gr.Blocks(title="VisionCrash AI") as demo:
    gr.Markdown(
        "# VisionCrash AI\n"
        "Upload a traffic/CCTV video to detect vehicle crashes using the trained TensorFlow Object Detection model."
    )
    with gr.Row():
        with gr.Column():
            video_input = gr.Video(label="Input Video")
            thresh_slider = gr.Slider(
                minimum=0.30,
                maximum=0.99,
                value=0.90,
                step=0.01,
                label="Detection Confidence Threshold",
            )
            alert_checkbox = gr.Checkbox(
                value=False,
                label="Send Email/SMS Alerts when crash is detected (requires configured secrets)",
            )
            run_btn = gr.Button("Run Crash Detection", variant="primary")
        with gr.Column():
            video_output = gr.Video(label="Annotated Output Video")
            frame_output = gr.Image(label="First Detected Crash Frame")
            status_output = gr.Textbox(label="Detection Status", lines=4)

    run_btn.click(
        fn=analyze_video,
        inputs=[video_input, thresh_slider, alert_checkbox],
        outputs=[video_output, frame_output, status_output],
    )

    if examples:
        gr.Examples(
            examples=examples,
            inputs=[video_input, thresh_slider, alert_checkbox],
        )


if __name__ == "__main__":
    demo.launch()
