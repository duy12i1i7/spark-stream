import cv2
import base64
from pyspark.sql import SparkSession
from ultralytics import YOLO

spark = SparkSession.builder.appName("VideoYOLO").getOrCreate()

model = YOLO("yolov8n.pt")

def detect_person(frame):
    results = model(frame)
    persons = []
    for box in results[0].boxes:
        if results[0].names[int(box.cls)] == 'person':
            x1, y1, x2, y2 = box.xyxy[0]
            persons.append((int(x1), int(y1), int(x2), int(y2)))
    return persons

def process_frame(frame):
    detections = detect_person(frame)
    for box in detections:
        x1, y1, x2, y2 = box
        cv2.rectangle(frame, (x1, y1), (x2, y2), color=(0, 255, 0), thickness=2)
        cv2.putText(frame, "person", (x1, y1-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
    return frame

def process_frame_with_save(frame_idx_tuple):
    idx, frame = frame_idx_tuple
    annotated_frame = process_frame(frame)
    ret, buffer = cv2.imencode('.jpg', annotated_frame)
    if not ret:
        return None
    image_base64 = base64.b64encode(buffer).decode('utf-8')
    return (idx, image_base64)

def main():
    video_path = "~/video.mp4"
    cap = cv2.VideoCapture(video_path)
    frames = []
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    cap.release()

    indexed_frames = spark.sparkContext.parallelize(list(enumerate(frames)), numSlices=8)

    results_rdd = indexed_frames.map(process_frame_with_save).filter(lambda x: x is not None)

    hdfs_output_path = "hdfs://node01:9000/annotated_frames"
    results_rdd.saveAsTextFile(hdfs_output_path)

if __name__ == "__main__":
    main()



