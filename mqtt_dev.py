import paho.mqtt.client as mqtt
import numpy as np
import base64
import zlib
import time

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str('machine/camera/jpeg_image'))
    # 將訂閱主題寫在on_connet中
    # 如果我們失去連線或重新連線時
    # 地端程式將會重新訂閱
    client.subscribe('machine/camera/jpeg_image_base64')
    print('mqtt connected')

# 當接收到從伺服器發送的訊息時要進行的動作
def on_message(client, userdata, msg):
    if(len(msg.payload) > 1000):
        print(f'topic:{msg.topic}')
        print(f"原始圖片{msg.payload}")


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
    client.connect("192.168.0.249", 1883, 60)
    # client.connect("172.20.10.8", 1883, 60)
    # -----------------------------------------------------------------------------------
    # 生成随机的800*600*3矩阵作为示例
    matrix = np.random.randint(0, 500, size=(800, 600, 3), dtype=int)

    # 压缩矩阵
    pre_time = time.time()
    compressed_data = zlib.compress(matrix.tobytes())
    print((time.time()-pre_time)*1000)
    # 将矩阵转换为Base64编码
    encoded_data = base64.b64encode(compressed_data)

    client.publish('machine/camera/jpeg_image_base64', encoded_data)

    client.loop_forever()
