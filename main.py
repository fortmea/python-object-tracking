import os
os.environ["KMP_DUPLICATE_LIB_OK"]="TRUE"
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "protocol_whitelist;file,http,https,tcp,tls,crypto,rtp,udp"
os.environ["YOLO_VERBOSE"] = "False"
import numpy as np
import supervision as sv
from ultralytics import YOLO
import cv2
import asyncio
import tkinter as tk
from tkinter import *
from typing import Dict
import numpy as np
from PIL import Image, ImageTk
import streamlink
import torch
from typing import *
import time
torch.cuda.set_device(0) # Set the GPU device to use. Remove if using CPU

model = YOLO("yolov8n.pt", verbose=False)
tracker = sv.ByteTrack()
box_annotator = sv.BoundingBoxAnnotator()
label_annotator = sv.LabelAnnotator()
trace_annotator = sv.TraceAnnotator()
EllipseAnnotator = sv.EllipseAnnotator()
MaskAnnotator = sv.MaskAnnotator()
dotAnnotator = sv.DotAnnotator()
triangleAnnotator = sv.TriangleAnnotator()
fps_monitor = sv.FPSMonitor()

stream_url = ""

def get_stream():
    streams = streamlink.streams(stream_url)
    if streams:
        return streams["best"].url
    else:
        return None

stream_url = get_stream()

if not stream_url:
    print("Error: Could not retrieve stream URL")
    exit()

cap = cv2.VideoCapture(stream_url)
global classFilter
classFilter = ""
global gDetections
gDetections = 0
buttons: List[tk.Button] = []
SelectedAnnotators: List = [box_annotator]

def callback(frame: np.ndarray, _: int) -> Tuple[np.ndarray, Dict]:
    results = model(frame)[0]
    detections = sv.Detections.from_ultralytics(results)
    dados = detections.data.copy()
    
    if(classFilter != ""):
        detections = detections[detections.data["class_name"] == classFilter]
    
    detections = tracker.update_with_detections(detections)
    global gDetections
    gDetections = len(detections)
    
    labels = [
        f"#{tracker_id} {results.names[class_id]}"
        for class_id, tracker_id
        in zip(detections.class_id, detections.tracker_id)
    ]
    
    for annotator in SelectedAnnotators:
        if(annotator == box_annotator):
            frame = box_annotator.annotate(frame, detections=detections)
        elif(annotator == label_annotator):
            frame = label_annotator.annotate(frame, detections=detections, labels=labels)
        elif(annotator == trace_annotator):
            frame = trace_annotator.annotate(frame, detections=detections)
        elif(annotator == EllipseAnnotator):
            frame = EllipseAnnotator.annotate(frame, detections=detections)
        elif(annotator == MaskAnnotator):
            frame = MaskAnnotator.annotate(frame, detections=detections)
        elif(annotator == dotAnnotator):
            frame = dotAnnotator.annotate(frame, detections=detections)
        elif(annotator == triangleAnnotator):
            frame = triangleAnnotator.annotate(frame, detections=detections)
            
    fps_monitor.tick()
    return [frame, dados]
    
def setFilter(classname: str):
    global classFilter
    classFilter = classname

def setAnnotator(annotator):
    global SelectedAnnotators
    if(annotator in SelectedAnnotators):
        SelectedAnnotators.remove(annotator)
    else:
        SelectedAnnotators.append(annotator)
        
async def show(annotator: np.ndarray, dados: Dict):
    fps_text = f'FPS: {int(fps_monitor.fps)}'
    global classFilter
    global gDetections
    cv2.putText(annotator, fps_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
    if(classFilter != ""):
        filterText = f'Filter: {classFilter}[{gDetections}]'
        cv2.putText(annotator, filterText, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
    image = Image.fromarray(cv2.cvtColor(annotator, cv2.COLOR_BGR2RGB))  
    
    photo = ImageTk.PhotoImage(image)
    
    if hasattr(show, "window"):
        show.window.img_label.configure(image=photo)
        show.window.img_label.image = photo
        #print(time.time()%5)
        if (int(time.time() % 10) == 0):
            
            unique_class_names = set(dados.get('class_name', []))
            if 'class_name' in dados:
                global buttons
                for i, class_name in enumerate(unique_class_names):
                    if(class_name not in [button.winfo_name() for button in buttons]):
                        cmd = lambda class_name=class_name: setFilter(class_name)
                        button = tk.Button(show.window, text=class_name, command=cmd, name=class_name)
                        button.grid(row=3+len(buttons), column=0, padx=5, pady=5)
                        buttons.append(button)
    else:
        show.window = tk.Toplevel()
        show.window.title("Frame")
        show.window.img_label = tk.Label(show.window)
        show.window.img_label.grid(row=1, column=1, padx=5, pady=5)
        button = tk.Button(show.window, text="All", command=lambda: setFilter(""))
        button.grid(row=2, column=0, padx=5, pady=5)
        button = tk.Button(show.window, text="Box", command=lambda: setAnnotator(box_annotator))
        button.grid(row=2, column=2, padx=5, pady=5)
        button = tk.Button(show.window, text="Label", command=lambda: setAnnotator(label_annotator))
        button.grid(row=3, column=2, padx=5, pady=5)
        button = tk.Button(show.window, text="Trace", command=lambda: setAnnotator(trace_annotator))
        button.grid(row=4, column=2, padx=5, pady=5)
        button = tk.Button(show.window, text="Ellipse", command=lambda: setAnnotator(EllipseAnnotator))
        button.grid(row=5, column=2, padx=5, pady=5)
        button = tk.Button(show.window, text="Mask", command=lambda: setAnnotator(MaskAnnotator))
        button.grid(row=6, column=2, padx=5, pady=5)
        button = tk.Button(show.window, text="Dot", command=lambda: setAnnotator(dotAnnotator))
        button.grid(row=7, column=2, padx=5, pady=5)
        button = tk.Button(show.window, text="Triangle", command=lambda: setAnnotator(triangleAnnotator))
        button.grid(row=8, column=2, padx=5, pady=5)
        
        
    show.window.img_label.configure(image=photo)
    show.window.img_label.image = photo
    
    show.window.update_idletasks()
    show.window.update()

def main():
    root = tk.Tk()
    if not cap.isOpened(): 
        print("Error: Could not open video stream or file")
        exit()
    while True:
        try:
            grabbed, frame = cap.read()
            if grabbed:
                annotator, dados = callback(frame, 0)
                asyncio.run(show(annotator, dados))
        except Exception as e:
            print(f"Error occurred: {e}")
main()
