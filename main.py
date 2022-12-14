import paho.mqtt.client as mqtt
import cv2
import numpy as np
from openvino.runtime import Core
import time
import matplotlib.pyplot as plt
import requests
from PIL import Image
# import binascii
import os
import threading



MQTT_Publish_topic = "machine/camera/SSD1"
MQTT_human_traffic = "machine/camera/humanTraffic"
MQTT_Perform_field1 = "machine/reference1/performance"

MQTT_SUBSCRIBER_topic_field2 = "machine/camera/ID_2/jpeg_image"
MQTT_Publish_topic_field2 = "machine/camera/ID_2/SSD1"
MQTT_human_traffic_field2 = "machine/camera/ID_2/humanTraffic"
MQTT_Perform_field2 = "machine/reference2/performance"
MQTT_Alert = "machine/alert"

classes = [
    "background", "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train",
    "truck", "boat", "traffic light", "fire hydrant", "street sign", "stop sign",
    "parking meter", "bench", "bird", "cat", "dog", "horse", "sheep", "cow", "elephant",
    "bear", "zebra", "giraffe", "hat", "backpack", "umbrella", "shoe", "eye glasses",
    "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball", "kite",
    "baseball bat", "baseball glove", "skateboard", "surfboard", "tennis racket", "bottle",
    "plate", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple",
    "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair",
    "couch", "potted plant", "bed", "mirror", "dining table", "window", "desk", "toilet",
    "door", "tv", "laptop", "mouse", "remote", "keyboard", "cell phone", "microwave", "oven",
    "toaster", "sink", "cupboard", "blender", "book", "clock", "vase", "scissors",
    "teddy bear", "hair drier", "toothbrush", "hair brush"
]

def process_results(frame, results, thresh=0.4):
    global human_traffic
    human_traffic = 0
    # The size of the original frame.
    h, w = frame.shape[:2]
    # The 'results' variable is a [1, 1, 100, 7] tensor.
    # results = results.squeeze()
    boxes = []
    labels = []
    scores = []
    for _, label, score, xmin, ymin, xmax, ymax in results:
        # Create a box with pixels coordinates from the box with normalized coordinates [0,1].
        boxes.append(
            tuple(map(int, (xmin * w, ymin * h, (xmax - xmin) * w, (ymax - ymin) * h)))
        )
        labels.append(int(label))
        scores.append(float(score))
        if(int(label) == 1):
            human_traffic += 1

    # Apply non-maximum suppression to get rid of many overlapping entities.
    # This algorithm returns indices of objects to keep.
    indices = cv2.dnn.NMSBoxes(
        bboxes=boxes, scores=scores, score_threshold=thresh, nms_threshold=0.8
    )
    # If there are no boxes.
    if len(indices) == 0:
        return []

    # Filter detected objects.
    return [(labels[idx], scores[idx], boxes[idx]) for idx in indices.flatten()]


def draw_boxes(select, frame, boxes):
    for label, score, box in boxes:
        # Choose color for the label.
        # Draw a box.
        x2 = box[0] + box[2]
        y2 = box[1] + box[3]
        if(label == 49 or label == 87):
            if(select == 1):
                client.publish(MQTT_Alert, "11")
            elif(select == 2):
                client.publish(MQTT_Alert, "12")
            cv2.rectangle(img=frame, pt1=box[:2], pt2=(x2, y2), color=(0, 0, 255), thickness=5)

        else:
            client.publish(MQTT_Alert, "0")
            cv2.rectangle(img=frame, pt1=box[:2], pt2=(x2, y2), color=(0, 255, 0), thickness=3)

        # Draw a label name inside the box.
        cv2.putText(
            img=frame,
            text=f"{classes[label]} {score:.2f}",
            org=(box[0] + 10, box[1] + 30),
            fontFace=cv2.FONT_HERSHEY_COMPLEX,
            fontScale=frame.shape[1] / 1000,
            color=(255, 0, 0),
            thickness=1,
            lineType=cv2.LINE_AA,
        )
        if(label == 49 or label == 87):
            url = "https://notify-api.line.me/api/notify"
            token = "GGfyfA0lv38uV5UbAYfPWTdGNOUwgh8cLClUbTNKcpG"
            headers = {
                'Authorization': 'Bearer ' + token
            }
            data = {
                'message':'警告! 發現危險物件'  # 設定要發送的訊息
            }
            result_image = cv2.imencode('.jpg', frame)[1]
            data_encode = np.array(result_image)
            imageFile = {'imageFile' : data_encode}   # 設定圖片資訊
            data = requests.post(url, headers=headers, data=data, files=imageFile)   # 發送

    return frame
# def detect_Object(frame):
def detect_Object(select, frame):
    global delay_list, mqtt_fps_list,mqtt_over_time,total_dalay,total_delay_sum
    start = time.time()
    mqtt_interval = (start - mqtt_over_time)* 1000
    mqtt_fps_list.append(mqtt_interval)
    global human_traffic
    original_img = frame
    str_payload = str(original_img)

    file_bytes = np.asarray(bytearray(frame), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    frame =img

    # origin_image = cv2.imread(filename="Street_people1.jpg")
    image = cv2.cvtColor(frame, code=cv2.COLOR_BGR2RGB)
    # print(f'origin_size:{image.shape}')
    image_resize = cv2.resize(src=image, dsize=(i_w, i_h))
    input_image = np.expand_dims(image_resize, 0)
    # print(f'resize:{input_image.shape}')
    image_resize.shape[0:2] #取第0、1個

    result_infer = compiled_model([input_image])[output_layer]
    boxes = result_infer[0,0]
    boxes = boxes[~(boxes == 0).all(1)]
    # print(f'origin boxes:{boxes}')

    # print(boxes)
    # boxes = boxes[(boxes >= 0).all(1)]
    # print(f'boxes finish{boxes}')

    boxes1 = process_results(frame=image, results=boxes)
    obj_frame = draw_boxes(select, frame=frame, boxes=boxes1)
    end = time.time()
    mqtt_over_time = end
    # print(f'{(end - start)* 1000} ms') #0.015s=15ms
    Perform = int((end - start)* 1000)
    # print(Perform)
    if(len(delay_list)>2000):
        for i in range(len(total_dalay)):
            if((int(total_dalay[i]))< 5000):
                total_delay_sum += int(total_dalay[i])
            else:
                print(int(total_dalay[i]))
        avg = total_delay_sum / len(total_dalay)
        print(f'sum:{total_delay_sum}')
        print(f'sum:{len(total_dalay)}')
        print(f'平均間隔時間{avg}')
        print(total_dalay[5:100])
        plt.subplot(3, 1, 1)
        plt.plot(delay_list)
        plt.title("Performer")
        plt.xlabel('Image data')
        plt.ylabel('Inference speed(ms)')
        plt.subplot(3, 1, 2)
        plt.plot(mqtt_fps_list[5:2000])
        plt.title("mqtt_fps")
        plt.xlabel('Image data')
        plt.ylabel('Intervals(ms)')
        plt.subplot(3, 1, 3)
        plt.plot(total_dalay[5:2000])
        plt.title("total_Delay")
        plt.xlabel('Image data')
        plt.ylabel('total_time(ms)')
        plt.show()

    else:
        refer_interval = (end - start)* 1000
        delay_list.append((end - start)* 1000)
        total_time = int(refer_interval + mqtt_interval)
        total_dalay.append(total_time)
    print(f"原始圖片{str_payload[0:100]}")
    print(f"推論時間:{Perform}ms")
    print(f"總耗費時間:{total_time}ms")
    print("----------------------------------------------------------")
    # cv2.imshow('esp32-cam pixel', obj_frame)
    # cv2.waitKey(1)

    # 11/22修改 將jpg格式圖檔轉Bytes
    result_image = cv2.imencode('.jpg', obj_frame)[1]
    data_encode = np.array(result_image)
    str_encode = data_encode.tobytes()
    #1 ID:1, 2 ID:2
    if(select == 1):
        # print("Field1 Refer")
        client.publish(MQTT_Publish_topic, str_encode)
        client.publish(MQTT_human_traffic, human_traffic)
        client.publish(MQTT_Perform_field1, Perform) #推論時間
    elif(select == 2):
        # print("Field2 Refer")
        client.publish(MQTT_Publish_topic_field2, str_encode)
        client.publish(MQTT_human_traffic_field2, human_traffic)
        client.publish(MQTT_Perform_field2, Perform) #推論時間

    #display data of mqtt
    # print(f'Send:{str_encode}')


# 當地端程式連線伺服器得到回應時，要做的動作
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str('machine/camera/jpeg_image'))
    # 將訂閱主題寫在on_connet中
    # 如果我們失去連線或重新連線時
    # 地端程式將會重新訂閱
    client.subscribe('machine/camera/jpeg_image')
    client.subscribe(MQTT_SUBSCRIBER_topic_field2)
    print('mqtt connected')
# 當接收到從伺服器發送的訊息時要進行的動作
def on_message(client, userdata, msg):
    if(len(msg.payload) > 1000):
        # print(msg.payload)
        # file_bytes = np.asarray(bytearray(msg.payload), dtype=np.uint8)
        # img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        # img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
        # img_people = cv2.imread('people.jpg')
        print(f'topic:{msg.topic}')
        # print(f"原始圖片{msg.payload}")
        if(msg.topic == 'machine/camera/jpeg_image'):
            detect_Object(1, msg.payload)
        elif(str(msg.topic) == MQTT_SUBSCRIBER_topic_field2):
            detect_Object(2, msg.payload)

if __name__ == "__main__":
    # 連線設定
    # 初始化地端程式
    # delay_list = []
    client = mqtt.Client()
    # 設定連線的動作
    client.on_connect = on_connect
    # 設定接收訊息的動作
    client.on_message = on_message
    # 設定登入帳號密碼
    #client.username_pw_set("try","xxxx")
    # 設定連線資訊(IP, Port, 連線時間)
    # client.connect("192.168.0.249", 1883, 60)
    client.connect("172.20.10.8", 1883, 60)
    # -----------------------------------------------------------------------------------
    ie = Core()
    print(ie.available_devices)

    model_ssd = "model/public/ssdlite_mobilenet_v2/FP16/ssdlite_mobilenet_v2.xml"
    model = ie.read_model(model=model_ssd)
    compiled_model = ie.compile_model(model=model_ssd, device_name="GPU")

    input_layer = compiled_model.input(0)
    output_layer = compiled_model.output(0)
    # print(input_layer)
    i_h, i_w = list(input_layer.shape)[1:3]
    # print(f'{i_h},{i_w}')
    input_layer.any_name, output_layer.any_name


    human_traffic = 0
    delay_list = []
    mqtt_fps_list = []
    mqtt_over_time = 0
    total_dalay = []
    total_delay_sum = 0
    # 開始連線，執行設定的動作和處理重新連線問題
    # 也可以手動使用其他loop函式來進行連接

    client.loop_forever()
    # client.loop_start()

