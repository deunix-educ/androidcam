'''
Created on 19 janv. 2023

@author: denis
'''
from threading import Event, Thread
from pathlib import Path
# opencv
#import cv2
#from kivy.uix.image import Image
#from kivy.graphics.texture import Texture  # @UnresolvedImport
#import numpy as np

# kivy.uix.camera
import io
from kivy.core.window import Window
from kivy.uix.camera import Camera
from PIL import Image as PILImage
#
from kivy.clock import Clock
from kivy.app import App
from kivy.properties import NumericProperty # StringProperty, ObjectProperty, BooleanProperty, ListProperty @UnresolvedImport
from kivy.logger import Logger, LOG_LEVELS
from kivy.utils import platform
import plyer
from . import utils
from .mqttmodule import VigiCamDaemon

Logger.setLevel(LOG_LEVELS["info"])

settings_file = 'vigicam-settings.yaml'
BASEDIR = Path(__file__).resolve().parent.parent
CONFIGFILE = BASEDIR / settings_file
SETTINGS = utils.yaml_load(CONFIGFILE)

if platform == 'android':
    from android.permissions import request_permissions, Permission # @UnresolvedImport
    request_permissions([
        Permission.CAMERA,
        Permission.WRITE_EXTERNAL_STORAGE,
        Permission.READ_EXTERNAL_STORAGE,        
        Permission.ACCESS_COARSE_LOCATION,
        Permission.ACCESS_FINE_LOCATION
    ])
    fileconf = plyer.storagepath.get_documents_dir()    #get_external_storage_dir()
    CONFIGFILE = f'{fileconf}/{settings_file}'
    try:
        SETTINGS = utils.yaml_load(CONFIGFILE)
    except:
        utils.yaml_save(CONFIGFILE, SETTINGS)
    
Logger.info(f"Load config file {CONFIGFILE}")    
    
TEXT = {
    "change_for": "Changer pour",
    "restart_app": "Relancer l'application",
    "quit": "Quitter l'application",
    "sure": "En êtes vous certain ?",
    "confirm": "Confirmer",
}

MQTT_MODE = {
    'public': 'réseau internet',
    'local': 'réseau local',
    'private': 'vpn',
}

IDX_MODE= {
    0: 'Caméra principale',
    1: 'Caméra frontale',
}

BT_STATE = {
    0: 'Envoyer',
    1: 'Stopper',
}

MQTT_CURRENT_MODE = MQTT_MODE.get(SETTINGS['config']['mqtt'])

#class CameraDevice(Image):
class CameraDevice(Camera):
    configfile = CONFIGFILE
    settings = SETTINGS
    config = settings['config']
    
    w, h = utils.dimensions(config.get('size'))   
    rear_cam = config.get('rear_cam', 0)
    front_cam = config.get('front_cam', 0)
    cam_index = NumericProperty(config.get('camid', 0))
    cam_rotate = NumericProperty(config.get('rotate', 0))
    cam_ratio = NumericProperty(w/h)
    
   
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Logger.info(f"Camera index={self.config.get('camid', 0)}  [ resolution: {self.resolution} max: {Window.size}]")
        self.app = App.get_running_app()
        self.app.lat = self.config.get('lat')
        self.app.lon = self.config.get('lon')
        self.wait_for_mqtt = Event()
        self.init()


    def init(self):
        try:
            """
            # opencv
            if platform == 'android':
                self.cap_api = cv2.CAP_ANDROID
            elif platform == 'linux':
                self.cap_api = cv2.CAP_V4L2"""
            self.mqttc = VigiCamDaemon(self, self.configfile, self.settings, self.config)
            Thread(target=self.worker, daemon=True).start()
            Logger.info(f"CameraDevice init wait for 5s")
            self.wait_for_mqtt.wait(5)

            self.video_capture_start()
        except Exception as e:
            Logger.info(f"CameraDevice init error\n{e}")


    def worker(self):
        Logger.info("Start VigiCamDaemon mqtt worker")
        self.mqttc.start_services()


    def video_capture_stop(self):
        # opencv
        #self.capture.release() 
        self.mqttc.stop_services()


    def video_capture_start(self):
        # opencv
        #self.capture = cv2.VideoCapture(self.cam_index, self.cap_api)
        #Logger.info(f"video_capture_start {self.capture}")
        self.counter = 0
        self.start()


    def start(self):
        fps = self.config.get('fps')
        Clock.schedule_interval(self.camera_read, 1.0/fps)
        Logger.info(f"Video Capture device={self.cam_index}, start playing={self.playing}, fps={fps}")


    def stop(self):
        Logger.info(f"Video Capture device {self.cam_index} halt")
        Clock.unschedule(self.camera_read)

       
    def camera_read(self, dt):
        try:    
            if self.playing:
                rate = float(self.config.get('zoom'))
                img = self.export_as_image()
                w, h = img._texture.size
                image = PILImage.frombytes('RGBA', (w, h), img._texture.pixels)
                image = image.convert('RGB')
                
                w, h= int(w * rate), int(h * rate)
                image = image.resize((w, h))
                imgByteArr = io.BytesIO()
                image.save(imgByteArr, "JPEG")
                frame = imgByteArr.getvalue()
                
                fps = self.config.get('fps')
                lat = 'NaN' if not self.app.lat else f'{self.app.lat:.6f}'
                lon = 'NaN' if not self.app.lon else f'{self.app.lon:.6f}'
                msg = f"[ {lat} - {lon} ]\n{self.counter} fps:{fps}"
                self.app.statusbar = msg
                self.mqttc.publish_bytes(f"{self.counter}/{lat}/{lon}/{fps}", frame)
                self.counter += 1

        except Exception as e:
            Logger.error(f"CameraDevice::camera_read error {e}")

    
    """
    # opencv
    def camera_read(self, dt):
        try:
            if self.mqttc.play:
                success, frame = self.capture.read()
                if success:
                    (h, w, _) = frame.shape                    
                    # kivy Image
                    buf = cv2.flip(frame, 0)                    
                    image_texture = Texture.create(size=(w, h), colorfmt='bgr')
                    image_texture.blit_buffer(buf.tostring(), colorfmt='bgr', bufferfmt='ubyte')
                    self.texture = image_texture
                    # end of kivy Image

                    # mqtt image
                    rate = float(self.config.get('zoom'))
                    frame = cv2.resize(frame, (int(w*rate), int(h*rate)) )
                    success, frame = cv2.imencode('.jpg', frame)
                    if success:
                        frame = frame.tobytes()
                        
                        fps = self.config.get('fps')
                        lat = 'NaN' if not self.app.lat else f'{self.app.lat:.6f}'
                        lon = 'NaN' if not self.app.lon else f'{self.app.lon:.6f}'
                        msg = f"[ {lat} - {lon} ]\n{self.counter} fps:{fps}"
                        self.app.statusbar = msg
                        self.mqttc.publish_bytes(f"{self.counter}/{lat}/{lon}/{fps}", frame)                       
                        self.counter += 1
                    # end of mqtt image
        except Exception as e:
            Logger.error(f"CameraDevice::camera_read error {e}")
    """
    

class Gps:
    is_gps = False
    gps = None
    def __init__(self, app=None):
        self.parent = app
        try:
            self.gps = plyer.gps
            self.gps.configure(on_location=self.parent.on_location, on_status=self.parent.on_status)
            self.is_gps = True
        except NotImplementedError:
            #import traceback
            #traceback.print_exc()
            Logger.info('Gps error: GPS is not implemented for your platform')

    def start(self, minTime=1000, minDistance=0):
        if self.is_gps:
            self.gps.start(minTime, minDistance)

    def restart(self, minTime=1000, minDistance=0):
        self.start(minTime, minDistance)

    def stop(self):
        if self.is_gps:
            self.gps.stop()

    def location(self, **kwargs):
        d = {}
        if self.is_gps:
            for k, v in kwargs.items():
                d[k]=v
        return d

    def status(self, stype, status):
        if self.is_gps:
            return stype, status
        return None, None

"""
def permissions(parent):

    def request_android_permissions(self):
        from android.permissions import request_permissions, Permission  # @UnresolvedImport

        def callback(permissions, results):
            if all([res for res in results]):
                print("callback. All permissions granted.")
            else:
                print("callback. Some permissions refused.")

        request_permissions([
            Permission.CAMERA,
            Permission.WRITE_EXTERNAL_STORAGE,
            Permission.READ_EXTERNAL_STORAGE,        
            Permission.ACCESS_COARSE_LOCATION,
            Permission.ACCESS_FINE_LOCATION], callback)
 """

