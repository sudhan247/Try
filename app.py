from sys import stdout
from flask import Flask, render_template, Response
from flask_socketio import SocketIO, emit
from PIL import Image
import threading, binascii, base64, logging, os, shutil, subprocess,signal 
from time import sleep
from io import BytesIO

global_dict = {"folder": None,"pic_num": 0}

def pil_image_to_base64(pil_image):
    buf = BytesIO()
    pil_image.save(buf, format="JPEG")
    return base64.b64encode(buf.getvalue())

def base64_to_pil_image(base64_img):
    return Image.open(BytesIO(base64.b64decode(base64_img)))

def ready_store():
    #Local storage to save
    current_directory = os.getcwd()
    final_directory = os.path.join(current_directory, r'garbage')
    global_dict["folder"] = final_directory
    if not os.path.exists(final_directory):
        os.makedirs(final_directory)
    else:
        shutil.rmtree(final_directory)
        os.makedirs(final_directory)

def initialise():
    #Kill old thread
    command = 'netstat -aon | find /i "listening" |find "5000"'
    c = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
    stdout, stderr = c.communicate();
    stdout = stdout.decode().strip().split()
    if "LISTENING" in stdout:   os.kill(int(stdout[-1]), signal.SIGTERM)
    ready_store()
class Camera(object):
    def __init__(self, makeup_artist):
        self.to_process = []
        self.to_output = []
        self.makeup_artist = makeup_artist
        thread = threading.Thread(target=self.keep_processing, args=())
        thread.daemon = True
        thread.start()
    def process_one(self):
        if not self.to_process:
            return
        input_str = self.to_process.pop(0)
        input_img = base64_to_pil_image(input_str)
        output_img = self.makeup_artist.apply_makeup(input_img)
        output_str = pil_image_to_base64(output_img)
        self.to_output.append(binascii.a2b_base64(output_str))
    def keep_processing(self):
        while True:
            self.process_one()
            sleep(0.01)
    def enqueue_input(self, input):
        self.to_process.append(input)
    def get_frame(self):
        while not self.to_output:
            sleep(0.05)
        return self.to_output.pop(0)

class Makeup_artist(object):
    def __init__(self):
        pass
    def apply_makeup(self, img):
        return img.transpose(Image.FLIP_TOP_BOTTOM)

app = Flask(__name__)
app.logger.disabled = True
app.config['SECRET_KEY'] = 'secret!'
app.config['DEBUG'] = True
socketio = SocketIO(app)

camera = Camera(Makeup_artist())

@socketio.on('input image', namespace='/test')
def test_message(input):
    input = input.split(",")[1]
    camera.enqueue_input(input)
    image_data = input
    with open(os.path.join(global_dict["folder"] ,"Record{0}.png".format(global_dict["pic_num"])), "wb") as fh:
        global_dict["pic_num"] += 1
        fh.write(base64.urlsafe_b64decode(image_data))
    image_data = "data:image/jpeg;base64," + image_data
    emit('out-image-event', {'image_data': image_data}, namespace='/test')

@socketio.on('connect', namespace='/test')
def test_connect():
    app.logger.info("client connected")

@app.route('/')
def index():
    global_dict["pic_num"] = 0
    ready_store()
    return render_template('index.html')

if __name__ == '__main__':
    initialise()
    socketio.run(app,use_reloader=False,log_output=False)
    

 