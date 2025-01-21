import pyrealsense2 as rs
import numpy as np
import cv2 as cv

from ultralytics import YOLO
from threading import Thread

from queue import Queue
import time

from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app=app)

class realsense:
    def __init__(self,serial_number:str):
        self.serial_number = serial_number
    
    def realsense_config(self):
        # Create a pipeline
        try:
            self.pipeline = rs.pipeline()
            config = rs.config()
            config.enable_device(self.serial_number)
            config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
            config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

            # Start streaming
            self.pipeline.start(config)

            align_to = rs.stream.color
            self.align = rs.align(align_to)
            return True
        except Exception as e:
            print(e)
            return False
    def realsense_stop(self):
        self.pipeline.stop()

def new_coordinates_after_resize_img(original_size, new_size, original_coordinate):
  original_size = np.array(original_size)
  new_size = np.array(new_size)
  original_coordinate = np.array(original_coordinate)
  xy = original_coordinate/(original_size/new_size)
  x, y = int(xy[0]), int(xy[1])
  return (x, y)

def calib_array_value(arr_np:np.ndarray) -> np.ndarray:
    mean1 = arr_np.mean()
    arr_np1 = arr_np[np.where(arr_np > mean1)]

    mean2 = arr_np.mean()
    arr_np2 = arr_np[np.where(arr_np < mean2)]

    if arr_np1.shape > arr_np2.shape:
        return arr_np1
    elif arr_np1.shape < arr_np2.shape:
        return arr_np2
    else:
        return arr_np2

def task_capture_frames_func(realsenses:list,queue_frames:Queue):
    while True:
        if not detect_human['enable']:
            time.sleep(1)
            continue
        try:
            list_detect = []
            index = 0
            for realsense in realsenses:
                frame = realsense.pipeline.wait_for_frames()
                # Align the depth frame to color frame
                aligned_frame = realsense.align.process(frame)
                # Get aligned frames
                aligned_depth_frame = aligned_frame.get_depth_frame() # aligned_depth_frame is a 640x480 depth image
                color_frame = aligned_frame.get_color_frame()
                # Validate that both frames are valid
                if not aligned_depth_frame or not color_frame:
                    continue
                color_image = np.asanyarray(color_frame.get_data())
                depth_image = np.asanyarray(aligned_depth_frame.get_data())

                if index == 0:
                    rot_color = cv.rotate(color_image,cv.ROTATE_90_CLOCKWISE)
                    rot_depth = cv.rotate(depth_image,cv.ROTATE_90_CLOCKWISE)
                elif index == 1:
                    rot_color = cv.rotate(color_image,cv.ROTATE_90_CLOCKWISE)
                    rot_depth = cv.rotate(depth_image,cv.ROTATE_90_CLOCKWISE)

                element = (rot_color,aligned_depth_frame,rot_depth)
                list_detect.append(element)
                index = index + 1
                print('unit',aligned_depth_frame.get_units())
            
            img_h = None
            depth_h = None
                
            if len(list_detect) == 2:
                img_h = cv.hconcat([list_detect[0][0],list_detect[1][0]])
                depth_h = cv.hconcat([list_detect[0][2],list_detect[1][2]])
            elif len(list_detect) == 1:
                img_h = cv.hconcat([list_detect[0][0],list_detect[0][0]])
                depth_h = cv.hconcat([list_detect[0][2],list_detect[0][2]])
            img_resize_dwn = cv.resize(img_h,dsize=None,fx=0.5,fy=0.5,interpolation=cv.INTER_CUBIC) #640,960
            img_resize_dwn[:,0:100] = [0,0,0]
            img_resize_dwn[:,382:] = [0,0,0]
            model = YOLO("yolo11n-seg.pt")
            results = model.predict(source=img_resize_dwn, save=False, classes=[0],imgsz=[320,480])

            arr_np = np.zeros(shape=(320,480),dtype=np.uint8)
            img_person_mask = arr_np.reshape(320,480)
            for result in results:
                masks = result.masks
                if masks != None:
                    for mask in masks:
                        mask_person = (mask.data[0].numpy())*255
                        person = mask_person.astype(np.uint8)
                        tmp = cv.bitwise_or(img_person_mask,person)
                        img_person_mask = tmp

            img_person_mask_rz_up = cv.resize(img_person_mask,dsize=None,fx=2,fy=2,interpolation=cv.INTER_CUBIC)
            person_mask = img_person_mask_rz_up == 0
            depth_person = np.ma.masked_array(depth_h,person_mask)

            list_rec = []
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    # confidence = box.conf[0]
                    class_id = int(box.cls[0])
                    class_name = model.names[class_id]
                    x1, y1, x2, y2 = box.xyxy[0]
                    # label = f"{class_name} {confidence:.2f}"
                    if class_name == "person":          
                        list_rec.append((int(x1),int(y1),int(x2),int(y2)))
            
            list_distance = []
            if len(list_rec) != 0:
                for rec in list_rec:
                    point1 = new_coordinates_after_resize_img((320,480), (640,960), (rec[0],rec[1]))
                    point2 = new_coordinates_after_resize_img((320,480), (640,960), (rec[2],rec[3]))

    
                    roi = depth_person[point1[1]:point2[1],point1[0]:point2[0]]
                    roi_zero = roi[np.nonzero(roi)]
                    calib_roi = calib_array_value(roi_zero)

                    if point1[0] >= 479:
                        distance = calib_roi.mean()*(list_detect[1][1].get_units())
                    else:
                        distance = calib_roi.mean()*(list_detect[0][1].get_units())
                    
                    distance = float(distance)
                    # distance = np.mean(roi[np.nonzero(roi)])*(list_detect[0][1].get_units())
                    
                    distance = round(distance,4)
                    list_distance.append(distance)
                    if distance < 2.8:
                        cv.putText(img_h, str(distance), (point1[0]+5, point1[1]+50), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 1)
                        cv.rectangle(img_h,point1,point2,(0,0,255),2)
                    else:
                        cv.putText(img_h, str(distance), (point1[0]+5, point1[1]+50), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 1)
                        cv.rectangle(img_h,point1,point2,(0,255,0),2)
            if len(list_distance) == 0:
                detect_human['human'] = False
            else:
                if min(list_distance) > detect_human['thres']:
                    detect_human['human'] = False
                else:
                    detect_human['human'] = True
            
            cv.imshow('win1',img_h)
            cv.imshow('win2',img_resize_dwn)
            
            if cv.waitKey(1) == ord('q'):
                break
        except Exception as e:
            print(e)
    realsense1.realsense_stop()
    realsense2.realsense_stop()

@app.route('/detect_human',methods=['POST'])
def detect_human_api():
    try:
        content = request.json
        keys = content.keys()
        if ('enable' in keys) and ('thres' in keys):
            detect_human['enable'] = content['enable']
            detect_human['thres'] = content['thres']
            return jsonify({"result":True,"desc":""}),201
        else:
            return jsonify({"result":False,"desc":""}),200
    except Exception as e:
        return jsonify({"result":False,"desc":str(e)}),500
@app.route('/check_human',methods=['GET'])
def check_human_api():
    try:
        if detect_human['enable']:
            return jsonify({"human":detect_human['human']}),200
        else:
            return jsonify({"human":True}),200
    except Exception as e:
        return jsonify({"result":False,"desc":str(e)}),500



if __name__ == '__main__':
    detect_human = {
        'enable': False,
        'thres': 2.0,
        'human': False
    }
    queue_frames = Queue(maxsize=1)
    realsense1 = realsense(serial_number='215222077273')
    realsense1.realsense_config()
    realsense2 = realsense(serial_number='213522072335')
    realsense2.realsense_config()

    task_capture_frames = Thread(target=task_capture_frames_func,args=(realsenses:=[realsense1,realsense2],queue_frames:=queue_frames))
    task_capture_frames.start()

    task_server = Thread(target=app.run,args=(host:='0.0.0.0',port:=8001))
    task_server.start()