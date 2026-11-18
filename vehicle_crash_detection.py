import threading
import time
from tkinter.ttk import Style
import tensorflow as tf
import cv2
import numpy as np
import tkinter as tk
import os
import json
from PIL import Image
from PIL import ImageTk
from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as viz_utils
from tkinter import ttk
import functools
import email_alert
import sms_alert
import datetime

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class VehicleCrash:
    def __init__(self, detections_update_label, content, button1):
        self.detections_update_label = detections_update_label
        self.content = content
        self.source = None
        self.running = False
        self.button1 = button1
        self.count = 0
        self.i = 0
        self.last_frame_path = ""
        self.last_label_path = ""
        self.current_video_output_path = ""
        self.last_record_timestamp = ""
        self._ensure_output_dirs()
    def set_source(self, source):
        self.source = source
    PATH_TO_SAVED_MODEL = os.path.join(_BASE_DIR, "inference_graph", "saved_model")
    HISTORY_PATH = os.path.join(_BASE_DIR, "outputs", "accident_history.jsonl")
    category_index = label_map_util.create_category_index_from_labelmap(
        os.path.join(_BASE_DIR, "label_map.pbtxt"),
        use_display_name=True)
    def _ensure_output_dirs(self):
        os.makedirs(os.path.join(_BASE_DIR, "outputs", "frame_img"), exist_ok=True)
        os.makedirs(os.path.join(_BASE_DIR, "outputs", "inside_label_img"), exist_ok=True)
        os.makedirs(os.path.join(_BASE_DIR, "outputs", "detection_video"), exist_ok=True)
    def _append_history(self):
        timestamp = datetime.datetime.now().isoformat(timespec="seconds")
        source_name = "Live-Camera" if self.source == 0 else str(self.source)
        record = {
            "timestamp": timestamp,
            "source": source_name,
            "frame_image": self.last_frame_path,
            "inside_label_image": self.last_label_path,
            "detection_video": self.current_video_output_path,
            "email_status": "Pending",
            "sms_status": "Pending",
        }
        with open(self.HISTORY_PATH, "a", encoding="utf-8") as history_file:
            history_file.write(json.dumps(record) + "\n")
        self.last_record_timestamp = timestamp
    def _update_last_history_status(self, email_status, sms_status):
        if not os.path.exists(self.HISTORY_PATH):
            return
        with open(self.HISTORY_PATH, "r", encoding="utf-8") as history_file:
            lines = history_file.readlines()
        for idx in range(len(lines) - 1, -1, -1):
            line = lines[idx].strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue

            if record.get("timestamp") == self.last_record_timestamp:
                record["email_status"] = email_status
                record["sms_status"] = sms_status
                lines[idx] = json.dumps(record) + "\n"
                break
        with open(self.HISTORY_PATH, "w", encoding="utf-8") as history_file:
            history_file.writelines(lines)
    def visualise_on_image(self, frame, image, bboxes, labels, scores, thresh):
        (h, w, d) = image.shape
        current_datetime = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
        for bbox, label, score in zip(bboxes, labels, scores):
            if score > thresh:
                xmin, ymin = int(bbox[1] * w), int(bbox[0] * h)
                xmax, ymax = int(bbox[3] * w), int(bbox[2] * h)
                cv2.rectangle(image, (xmin, ymin), (xmax, ymax), (0, 0, 255), 2)
                cv2.putText(image, f"{label}: {int(score * 100)} %", (xmin, ymin), cv2.FONT_HERSHEY_SIMPLEX, 1,
                            (255, 255, 255), 2)
                self.count += 1
                print(self.count)
                if (self.count == 5):
                    label_box_image = frame[ymin:ymax, xmin:xmax]
                    self.last_frame_path = os.path.join(_BASE_DIR, "outputs", "frame_img", "vcd_frame" + str(current_datetime) + str(self.i) + ".jpg")
                    cv2.imwrite(self.last_frame_path, image)
                    image_size = (1920, 1080)
                    resized_image = cv2.resize(label_box_image, image_size)
                    kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
                    sharpened_image = cv2.filter2D(resized_image, -1, kernel)
                    png_quality = 100
                    self.last_label_path = os.path.join(_BASE_DIR, "outputs", "inside_label_img", "vcd_inlabel" + str(current_datetime) + str(self.i) + ".png")
                    cv2.imwrite(self.last_label_path,
                                sharpened_image,
                                [int(cv2.IMWRITE_JPEG_QUALITY), png_quality])
                if (self.count == 20):
                    print("Vehicle_Crash_Detected")
                    self._append_history()
                    perform_label_detected_func = threading.Thread(target=self.perform_label_detected)
                    perform_label_detected_func.start()
                    self.i += 1
                    self.count = 0
                    break
        return image
    def update_progress(self, progress, value):
        progress['value'] = value
        progress.update()
    def perform_label_detected(self):
        self.detections_update_label.configure(text="Vehicle Crash has been Detected")
        email_status = "Email not attempted"
        sms_status = "SMS not attempted"
        try:
            em = email_alert.Email(self.source)
            em.run_mail()
            email_status = "Email sent"
            self.detections_update_label.configure(
                text="Email Alert Send Successfully to nearby Hospital,Police Station and RTO")
        except Exception as exc:
            email_status = f"Email failed: {exc}"
            self.detections_update_label.configure(text="Email alert failed")
        time.sleep(0.5)
        sm = sms_alert.Sms(self.source)
        sms_ok, sms_message = sm.run_sms()
        sms_status = sms_message
        if sms_ok:
            self.detections_update_label.configure(
                text="SMS Alert Send Successfully to nearby Hospital,Police Station and RTO")
        else:
            self.detections_update_label.configure(text="SMS alert failed or skipped")
        self._update_last_history_status(email_status, sms_status)
        time.sleep(0.5)
        if email_status == "Email sent" and sms_ok:
            self.detections_update_label.configure(
                text="Email and SMS Alert Send Successfully to nearby Hospital,Police Station and RTO")
        else:
            self.detections_update_label.configure(text="Alert processing completed with warnings")
        time.sleep(0.5)
        self.detections_update_label.configure(text="")
    detect_fn = ""
    @functools.lru_cache(maxsize=None)
    def load_model(self):
        style = Style()
        style.theme_use('alt')
        style.configure("Horizontal.TProgressbar", troughcolor='white', background='black', thickness=30)
        progress = ttk.Progressbar(self.content, orient=tk.HORIZONTAL, style="Horizontal.TProgressbar", length=300,
                                   mode='determinate')
        progress.pack(side="bottom", pady=(0, 30))
        self.detections_update_label.configure(text="Loading 0%")
        self.update_progress(progress, 0)
        time.sleep(0.1)
        print("Loaded 10% saved model ...")
        self.update_progress(progress, 10)
        self.detections_update_label.configure(text="Loading .10%")
        time.sleep(0.1)
        global detect_fn
        print("Loading saved model ...")
        detect_fn = tf.saved_model.load(self.PATH_TO_SAVED_MODEL)
        print("Loaded 50% saved model ...")
        self.detections_update_label.configure(text="Loading ....50%")
        self.update_progress(progress, 50)
        time.sleep(1.5)
        print("Model Loaded!")
        self.detections_update_label.configure(text="Loading .........100%")
        self.update_progress(progress, 100)
        time.sleep(1.5)
        self.detections_update_label.configure(text="")
        time.sleep(0.1)
        progress.destroy()
        return detect_fn
    def close_canvas(self, canvas):
        canvas.destroy()
        self.content.update()
    def run_detection(self):
        self.running = True
        while self.running:
            if self.source in (None, "Video Source"):
                self.detections_update_label.configure(text="Please select a video source first")
                self.running = False
                break
            print("Video Source : ", self.source)
            video_capture = cv2.VideoCapture(self.source)
            start_time = time.time()
            canvas = tk.Canvas(self.content, width=1000, height=600)
            canvas.pack(side="top", anchor="n", padx=10, pady=40)
            frame_width = int(video_capture.get(3))
            frame_height = int(video_capture.get(4))
            size = (frame_width, frame_height)
            video_timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            self.current_video_output_path = os.path.join(_BASE_DIR, "outputs", "detection_video", f"det_vid_{video_timestamp}.mp4")
            result = cv2.VideoWriter(self.current_video_output_path, cv2.VideoWriter.fourcc('m', 'p', '4', 'v'),
                                     15,
                                     size)
            while True:
                if not self.running:
                    break   
                ret, frame = video_capture.read()
                if not ret:
                    self.close_canvas(canvas)
                    self.stop_detection()
                    self.button1.config(text="Detection \nOFF")
                    self.detections_update_label.configure(text="")
                    self.source = "Video Source"
                    print('Unable to read video / Video ended')
                    self.detections_update_label.configure(text="Unable to read video / Video ended")
                    break
                frame = cv2.flip(frame, 1)
                image_np = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                input_tensor = tf.expand_dims(tf.convert_to_tensor(image_np), axis=0)
                detections = detect_fn(input_tensor)
                score_thresh = 0.90
                max_detections = 1
                scores = detections['detection_scores'][0, :max_detections].numpy()
                bboxes = detections['detection_boxes'][0, :max_detections].numpy()
                labels = detections['detection_classes'][0, :max_detections].numpy().astype(np.int64)
                labels = [self.category_index[n]['name'] for n in labels]
                self.visualise_on_image(frame, frame, bboxes, labels, scores, score_thresh)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image = Image.fromarray(frame)
                image = image.resize((1000, 600))
                photo = ImageTk.PhotoImage(image)
                end_time = time.time()
                fps = int(1 / (end_time - start_time))
                start_time = end_time
                canvas.create_image(0, 0, image=photo, anchor=tk.NW)
                canvas.create_text(50, video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT) + 25, text=f"FPS: {fps}",
                                   font=("Arial", 14), fill="red", anchor=tk.NW)
                canvas.update()
                result.write(frame)
            video_capture.release()
            result.release()
    def stop_detection(self):
        self.running = False
        self.count = 0
        print("Detection Stopped")
