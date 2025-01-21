import cv2
from ultralytics import YOLO
import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
import os
import threading
import time
from zipfile import ZipFile
import webbrowser
import json
from queue import Queue
import pyrealsense2 as rs
import numpy as np

pipeline = rs.pipeline()
config = rs.config()
config.enable_device('105322250851')
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

pipeline.start(config)
depth_sensor= pipeline.get_active_profile().get_device().first_depth_sensor()
depth_sensor. set_option(rs.option.depth_units, 0.0001)
depth_sensor.set_option(rs.option.visual_preset,3)

area_queue = Queue(maxsize=10)

# Load YOLO model
model = YOLO("yolov10n.pt")
# Directories for training and validation data
train_data_dir = "datasets/data/train_data"
val_data_dir = "datasets/data/val_data"
pic_data_dir = "datasets/data/pic_data"

# Ensure directories exist
os.makedirs(train_data_dir, exist_ok=True)
os.makedirs(val_data_dir, exist_ok=True)

# Initialize Tkinter GUI
window = tk.Tk()
window.title("YOLO Detection and Data Collection")

# Create frames for layout
left_frame = tk.Frame(window)
left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
right_frame = tk.Frame(window)
right_frame.pack(side=tk.RIGHT, fill=tk.Y)

# Canvas to display images
canvas = tk.Canvas(left_frame, width=800, height=600)
canvas.pack()

# Create a canvas and a scrollbar for thumbnails
thumbnail_canvas = tk.Canvas(right_frame, width=100)
thumbnail_scrollbar = tk.Scrollbar(right_frame, orient=tk.VERTICAL, command=thumbnail_canvas.yview)
thumbnail_scrollable_frame = tk.Frame(thumbnail_canvas)

thumbnail_scrollable_frame.bind(
    "<Configure>",
    lambda e: thumbnail_canvas.configure(scrollregion=thumbnail_canvas.bbox("all"))
)

thumbnail_canvas.create_window((0, 0), window=thumbnail_scrollable_frame, anchor="nw")
thumbnail_canvas.configure(yscrollcommand=thumbnail_scrollbar.set)

thumbnail_canvas.pack(side=tk.LEFT, fill=tk.Y, expand=True)
thumbnail_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# Video capture thread variables
frame = None
stop_thread = False
mode = ""

# Function to start video capture in a separate thread
def video_capture_thread():
    global frame, stop_thread
    while not stop_thread:
        frames = pipeline.wait_for_frames()
        depth_frame  = frames.get_depth_frame()
        color_frame  = frames.get_color_frame()
        frame = np.asanyarray(color_frame.get_data())
# Start video capture thread
thread = threading.Thread(target=video_capture_thread)
thread.start()

# Function to switch between modes
def select_model_file():
    global mode
    if mode != 'detect':
        button_model['text']= "Mode Detect"
        switch_mode("detect")
        model_file = tk.filedialog.askopenfilename(
            title="Select YOLO model file",
            filetypes=[("PyTorch Model Files", "*.pt")],
            initialdir="runs/detect"  # Set initial directory to 'runs/detect'
        )

        # If a file is selected, load the model
        if model_file:
            global model
            model = YOLO(model_file)  # Load the selected model
            print(f"Model {model_file} loaded successfully.")
            switch_mode("detect")  # Switch to detect mode
    else:
        button_model["text"] = 'Mode Capture'
        switch_mode('capture')

def switch_mode(new_mode):
    global mode
    mode = new_mode
    print(f"Mode: {mode}")

# Function to update the thumbnails frame
def update_image_thumbnails():
    # Clear the current thumbnails
    for widget in thumbnail_scrollable_frame.winfo_children():
        widget.destroy()

    # Load and display thumbnails
    for filename in sorted(os.listdir(pic_data_dir)):
        if filename.endswith(".jpg"):
            image_path = os.path.join(pic_data_dir, filename)
            img = Image.open(image_path)
            img.thumbnail((80, 80))  # Resize image to thumbnail size
            img_tk = ImageTk.PhotoImage(img)
            label = tk.Label(thumbnail_scrollable_frame, image=img_tk)
            label.image = img_tk  # Keep a reference to avoid garbage collection
            label.pack(pady=2)

# Function to save cropped image and label
def save_captured_image():
    global frame, image_count, pic_data_dir, mode
    switch_mode('none')
    if (frame is not None):
        # Convert the frame to RGB format
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(frame_rgb)

        # Generate a sequential filename
        filename = f"{image_count:03d}.jpg"
        filepath = os.path.join(pic_data_dir, filename)

        # Save the image
        image.save(filepath)
        print(f"Saved image: {filepath}")

        # Increment the image count
        image_count += 1

        # Update the thumbnails to reflect the new image
        update_image_thumbnails()
def rectangles_intersect(x1, y1, x2, y2, x3, y3, x4, y4):
    # Check if one rectangle is to the left of the other
    if x2 < x3 or x4 < x1:
        return False
    # Check if one rectangle is above the other
    if y2 < y3 or y4 < y1:
        return False
    return True
# Function to perform object detection
def detect_objects():
    global frame
    if frame is not None:
        results = model.track(frame)
        for result in results:
            boxes = result.boxes
            for box in boxes:
                # Get the bounding box coordinates
                x1, y1, x2, y2 = box.xyxy[0]
                confidence = box.conf[0]
                # Get the class ID and name
                class_id = int(box.cls[0])
                class_name = model.names[class_id]

                # Draw the bounding box
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (255, 0, 0), 2)

                # Display the class name and confidence score
                label = f"{class_name} {confidence:.2f}"
                cv2.putText(frame, label, (int(x1), int(y1) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
# Function to update frame on canvas
def update_frame():
    global frame
    if frame is not None:
        if mode == "detect":
            detect_objects()
        # Convert the resized frame to RGB format
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)

        # Create a PhotoImage for displaying on the Tkinter canvas
        img_tk = ImageTk.PhotoImage(image=img)
        canvas.create_image(0, 0, anchor=tk.NW, image=img_tk)
        canvas.image = img_tk

    window.after(10, update_frame)

# Function to start YOLO training
def train_model():
    global model
    print("Starting training...")

    # Simulate a training process and update progress bar
    epochs = 150  # Total number of epochs
    steps_per_epoch = 100  # Total steps per epoch, adjust if needed
    total_steps = epochs * steps_per_epoch  # Total steps for the entire training
    
    for epoch in range(epochs):
        for step in range(steps_per_epoch):
            # Simulate each step by updating the progress
            progress = ((epoch * steps_per_epoch) + step + 1) / total_steps * 100
            progress_bar["value"] = progress  # Update the progress bar
            window.update_idletasks()  # Update the Tkinter GUI
            print(f"Epoch {epoch + 1}/{epochs}, Step {step + 1}/{steps_per_epoch}")

        # Optional: After each epoch, you can add a small delay to simulate training time
        time.sleep(0.1)

    # Start the actual training process
    try:
        model.train(data="data.yaml", epochs=epochs)
    except FileNotFoundError as e:
        print(f"Error: {e}")

    progress_bar["value"] = 100  # Set the progress bar to 100% after training completes
    print("Training completed.")

def extract_zip_file():
    zip_file_path = filedialog.askopenfilename(
        title="Select a ZIP File",
        filetypes=[("ZIP Files", "*.zip")]
    )

    if zip_file_path:
        # Directory where extracted files will be saved
        extract_directory = os.path.join(os.getcwd(), "datasets/data/train_data")
        extract_directory_val = os.path.join(os.getcwd(), "datasets/data/val_data")

        # Ensure the extraction directory exists
        os.makedirs(extract_directory, exist_ok=True)
        os.makedirs(extract_directory_val, exist_ok=True)

        with ZipFile(zip_file_path, 'r') as zip_ref:
            for file_name in zip_ref.namelist():
                if file_name.startswith("images/") and not file_name.endswith("/"):
                    # Extract the file, ignoring the 'images/' prefix
                    file_path = file_name[len("images/"):]
                    target_path = os.path.join(extract_directory, file_path)
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    with open(target_path, "wb") as f:
                        f.write(zip_ref.read(file_name))
                if file_name.startswith("labels/") and not file_name.endswith("/"):
                    # Extract the file, ignoring the 'images/' prefix
                    file_path = file_name[len("labels/"):]
                    target_path = os.path.join(extract_directory, file_path)
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    with open(target_path, "wb") as f:
                        f.write(zip_ref.read(file_name))

                if file_name.startswith("images/") and not file_name.endswith("/"):
                    # Extract the file, ignoring the 'images/' prefix
                    file_path = file_name[len("images/"):]
                    target_path = os.path.join(extract_directory_val, file_path)
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    with open(target_path, "wb") as f:
                        f.write(zip_ref.read(file_name))
                if file_name.startswith("labels/") and not file_name.endswith("/"):
                    # Extract the file, ignoring the 'images/' prefix
                    file_path = file_name[len("labels/"):]
                    target_path = os.path.join(extract_directory_val, file_path)
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    with open(target_path, "wb") as f:
                        f.write(zip_ref.read(file_name))

        print(f"Extracted 'images', 'labels' folder from {zip_file_path} to 'data'")
        update_image_thumbnails()

def open_website():
    url = "http://127.0.0.1:8080/"  # Replace with your desired URL
    webbrowser.open(url)
# Initialize image counter
image_count = 1

# Create progress bar for training
progress_bar = ttk.Progressbar(window, length=300, mode="determinate")
progress_bar.pack(pady=20)

# Add buttons
button_train = tk.Button(window, text="Train Model", command=train_model, width=30)
button_train.pack(pady=10)

button_extract = tk.Button(window, text="Extract ZIP", command=extract_zip_file, width=30)
button_extract.pack(pady=10)

button_capture = tk.Button(window, text="Capture Image", command=save_captured_image, width=30)
button_capture.pack(pady=10)

button_model = tk.Button(window, text="Mode Capture", command=select_model_file, width=30)
button_model.pack(pady=10)

button_open_web = tk.Button(window, text="Open Website", command=open_website, width=30)
button_open_web.pack(pady=10)

update_image_thumbnails()
# Start frame update loop
window.after(10, update_frame)

# Start Tkinter mainloop
window.mainloop()

# Stop the video capture thread when the program ends
stop_thread = True
pipeline.stop()
cv2.destroyAllWindows()
