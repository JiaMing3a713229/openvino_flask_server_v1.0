from flask import Flask, render_template, Response, make_response
from flask_mqtt import Mqtt

app = Flask(__name__)

app.config['MQTT_BROKER_URL'] = '192.168.139.106'
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_USERNAME'] = ""
app.config['MQTT_PASSWORD'] = ""
app.config['MQTT_KEEPALIVE'] = 5
app.config['MQTT_TLS_ENABLED'] = False

mqtt_client = Mqtt(app)

TOPICS = {'stream_res1': "machine/camera/jpeg_image",
        'topic_classify_ref' : "machine/camera/SSD1",
        'topic_human_traffic' : "machine/camera/humanTraffic",
        'topic_Perform_field1' : "machine/reference1/performance",
        'stream_res2': "machine/camera/ID_2/jpeg_image",
        'topic_classify_ref_field2' : "machine/camera/ID_2/SSD1",
        'topic_human_traffic_field2' : "machine/camera/ID_2/humanTraffic",
        'topic_Perform_field2':"machine/reference2/performance",
        'MQTT_Alert' : "machine/alert"
}

stream_data = {'stream_img1': b"", 'stream_img2': b"", 'reference_img': b"", 'reference_img2': b""}


topic_stream1 = "machine/camera/jpeg_image"
topic_classify_ref = "machine/camera/SSD1"
topic_human_traffic = "machine/camera/humanTraffic"
topic_Perform_field1 = "machine/reference1/performance"

topic_stream_field2 = "machine/camera/ID_2/jpeg_image"
topic_classify_ref_field2 = "machine/camera/ID_2/SSD1"
topic_human_traffic_field2 = "machine/camera/ID_2/humanTraffic"
topic_Perform_field2 = "machine/reference2/performance"

MQTT_Alert = "machine/alert"

def get_stream():
    while True:
        yield (b'--frame\r\n' b'Content-Type:image/jpeg\r\n\r\n' +
               bytearray(stream_data['stream_img1']) + b'\r\n')

def get_stream_field2():
    global stream_img2
    while True:
        yield (b'--frame\r\n' b'Content-Type:image/jpeg\r\n\r\n' +
               bytearray(stream_img2) + b'\r\n')

def get_stream_refer():
    global reference_img
    while True:
        yield (b'--frame\r\n' b'Content-Type:image/jpeg\r\n\r\n' +
               bytearray(reference_img) + b'\r\n')
def get_stream_refer_field2():
    global reference_img2
    while True:
        yield (b'--frame\r\n' b'Content-Type:image/jpeg\r\n\r\n' +
               bytearray(reference_img2) + b'\r\n')


def get_humanTraffic():
    global humanTraffic
    while True:
        yield humanTraffic

@mqtt_client.on_connect()
def handle_connect(client, userdata, flags, rc):
    if rc==0:
        print('Connectd successfully')
        for topic in TOPICS.values():
            mqtt_client.subscribe(topic = topic)
    else:
        print('Bad connection code', rc)

@mqtt_client.on_message()
def handle_mqtt_message(client, userdata, message):
    global reference_img, humanTraffic, performance
    global stream_img2, reference_img2, humanTraffic_field2, performance_field2
    global alert_flag
    topic = message.topic
    payload = message.payload

    if(topic == TOPICS['stream_res1']):
        stream_data['stream_img1'] = payload
        print("Img1 Receive!")
    elif(topic == topic_classify_ref):
        reference_img = payload
    elif(topic == topic_human_traffic):
        humanTraffic = int(payload)
        # print(f'humanTraffic{humanTraffic}')
    elif(topic == topic_stream_field2):
        stream_img2 = payload
    elif(topic == topic_classify_ref_field2):
        reference_img2 = payload
    elif(topic == topic_human_traffic_field2):
        humanTraffic_field2 = payload
        # print(f'humanTraffic{humanTraffic_field2}')
    elif(topic == topic_Perform_field1):
        performance = payload
    elif(topic == topic_Perform_field2):
        performance_field2 = payload
    elif(topic == MQTT_Alert):
        alert_flag = payload

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/monitor")
def image_stream1():
    stream_str = str(stream_data['stream_img1'])
    # web_data = {
    #     "humanTraffic" :humanTraffic,
    #     "stream_str": stream_str
    # }
    # return render_template("monitor.html", web_data = web_data)
    return render_template("monitor_v1.html")

@app.route("/monitor_field2")
def image_stream2():
    global stream_img2
    stream_str = str(stream_img2)
    web_data = {
        "humanTraffic" :humanTraffic,
        "stream_str": stream_str
    }
    return render_template("monitor2.html", web_data = web_data)
@app.route("/monitor_total")
def image_stream_total():
    return render_template("monitor_total.html")



@app.route("/stream_feed")
def stream_feed():
    return Response(get_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')
@app.route("/stream_reference")
def stream_reference():
    return Response(get_stream_refer(), mimetype='multipart/x-mixed-replace; boundary=frame')
@app.route("/humanTraffic_data")
def humanTraffic_data():
    global humanTraffic
    resp = make_response(str(humanTraffic))
    resp.mimetype = "text/plain"
    return resp

# 場域2之 資料串流
@app.route("/stream_feed_field2")
def stream_feed_field2():
    return Response(get_stream_field2(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/stream_reference_field2")
def stream_reference_field2():
    return Response(get_stream_refer_field2(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/humanTraffic_data_field2")
def humanTraffic_data_field2():
    global humanTraffic_field2
    humanTraffic = int(humanTraffic_field2)
    resp2 = make_response(str(humanTraffic))
    resp2.mimetype = "text/plain"
    return resp2

@app.route("/performance_1")
def performance_1():
    global performance
    performance = int(performance)
    resp2 = make_response(str(performance))
    resp2.mimetype = "text/plain"
    return resp2

@app.route("/performance_2")
def performance_2():
    global performance_field2
    performance = int(performance_field2)
    resp2 = make_response(str(performance))
    resp2.mimetype = "text/plain"
    return resp2


@app.route("/alert")
def alert():
    global alert_flag
    alert = int(alert_flag)
    resp2 = make_response(str(alert))
    resp2.mimetype = "text/plain"
    return resp2

if __name__ == "__main__":
    # stream_img1 = ""
    stream_img2 = ""
    reference_img = ""
    reference_img2 = ""
    humanTraffic = 0
    humanTraffic_field2 = 0
    performance = 0
    performance_field2 = 0
    alert_flag = 0

    app.run(debug = True, host="0.0.0.0", port=3000)
