import paho.mqtt.client as mqtt
import numpy as np
import base64
import zlib

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
        # 解码收到的Base64编码
        decoded_data = base64.b64decode(msg.payload)

        # 将Base64解码后的数据转换回矩阵
        matrix = np.frombuffer(zlib.decompress(decoded_data), dtype=int).reshape((800, 600, 3))

        # 打印矩阵的形状和数据类型
        print("Matrix shape:", matrix.shape)
        print("Matrix dtype:", matrix.dtype)
        print(matrix)

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
    client.loop_forever()
