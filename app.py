from flask import Flask, Response, render_template
import base64
from hdfs import InsecureClient
import cv2
import numpy as np

app = Flask(__name__)

hdfs_client = InsecureClient('http://node01:9870', user='hadoop')

def load_frames_from_hdfs(hdfs_path):
    frames = {}
    file_list = hdfs_client.list(hdfs_path)
    for file_name in file_list:
        with hdfs_client.read(f"{hdfs_path}/{file_name}", encoding='utf-8') as reader:
            for line in reader:
                frame_id, img_str = eval(line.strip())
                frames[int(frame_id)] = img_str
    ordered_frames = [frames[i] for i in sorted(frames.keys())]
    return ordered_frames

def generate_video_stream():
    hdfs_path = "/annotated_frames"
    frame_base64_list = load_frames_from_hdfs(hdfs_path)
    for img_str in frame_base64_list:
        img_bytes = base64.b64decode(img_str)
        nparr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        ret, jpeg = cv2.imencode('.jpg', frame)
        if not ret:
            continue
        frame_bytes = jpeg.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_video_stream(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)






