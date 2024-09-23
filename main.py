#!.venv/bin/python
'''
python-for-android, pyjnius
kivy-ios, pyobjus

Created on 14 mars 2022
@author: denis
'''
#import cv2
from kivy.app import App
from kivy.clock import mainthread
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.core.window import Window

# ObjectProperty, NumericProperty, BooleanProperty, ListProperty, StringProperty
from kivy.properties import StringProperty, BooleanProperty  # @UnresolvedImport
from kivy.logger import Logger, LOG_LEVELS
from contrib import cameramodule as module

Logger.setLevel(LOG_LEVELS["info"])


class Vigicam(module.CameraDevice):
    playing = BooleanProperty(True)

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        self.mqtt = self.settings.get('mqtt', 'private')


    def textpopup(self, title='', text=''):
        box = BoxLayout(orientation='vertical')
        box.add_widget(Label(text=text))
        mybutton = Button(text=f"{module.TEXT.get('sure')}", size_hint=(1, 1),color=(1, 1, 1, 1) )
        box.add_widget(mybutton)
        popup = Popup(title=title, content=box, size_hint=(None, None), size=(640, 480))
        mybutton.bind(on_release=self.save_config)
        popup.open()


    def set_text_button(self, button):
        button.text = module.BT_STATE.get(self.playing)


    def send_video(self, instance):
        self.playing = not self.playing
        #self.set_text_button(instance)
        if self.playing:
            Logger.info(f"Start recording")
            self.mqttc.play = True
        else:
            Logger.info(f"Cancel recording")
            self.mqttc.play = False


    def change_camera_index(self, instance):
        self.cam_index = self.front_cam if self.cam_index == self.rear_cam  else self.rear_cam
        #self.capture.release()
        #self.capture = cv2.VideoCapture(self.cam_index, self.cap_api)
        Logger.info(f"change_camera_index  {self.cam_index}")


    def rotate(self, instance):
        self.cam_rotate -= 90
        if self.cam_rotate <= -360:
            self.cam_rotate = 0
        Logger.info(f"Camera rotate {self.cam_rotate}")
        self.config['rotate'] =  self.cam_rotate
        self.mqttc.save_config()

    
    def change_mqtt_network(self, instance):
        self.mqtt = 'private' if self.mqtt == 'public' else 'public'
        Logger.info(f"change_mqtt_network pour {self.mqtt}")
        self.textpopup(
            title=f'{module.TEXT.get("change_for")} {module.MQTT_MODE.get(self.mqtt)}', 
            text=f'{module.TEXT.get("restart_app")}'
        )

    def save_config(self, instance):
        self.config['mqtt'] = self.mqtt
        Logger.info(f"save_config  {self.mqtt}")
        self.mqttc.save_config()
        self.app.stop()


    def stop_video(self, button):
        self.playing = False
        self.set_text_button(button)


    def app_quit(self, instance):
        Logger.info("quit_action")
        self.app.on_request_close()


class VigiCamera(App):
    gps = None
    lat = None
    lon = None
    alt = None

    statusbar = StringProperty('')
    title = StringProperty(f"Camera {module.MQTT_CURRENT_MODE}")


    def build(self):
        Window.bind(on_request_close=self.on_request_close)
        #return Vigicam()


    def on_request_close(self, *args):
        self.textpopup(title=f"{module.TEXT.get('quit')}", text=f"{module.TEXT.get('sure')}")
        return True


    def textpopup(self, title='', text=''):
        box = BoxLayout(orientation='vertical')
        box.add_widget(Label(text=text))
        mybutton = Button(text=f"{module.TEXT.get('confirm')}", size_hint=(1, 1),color=(1, 1, 1, 1) )
        box.add_widget(mybutton)
        popup = Popup(title=title, content=box, size_hint=(None, None), size=(640, 480))
        mybutton.bind(on_release=self.stop)
        popup.open()


    def on_start(self):
        Logger.info("VigiCamera on_start")
        self.gps = module.Gps(self)
        self.gps.start()
        #self.root.ids.camera.set_text_button(self.root.ids.bt_rec)


    def on_stop(self):
        Logger.info("VigiCamera on_stop")
        self.root.ids.camera.video_capture_stop()
        self.gps.stop()


    def on_pause(self):
        Logger.info("VigiCamera on_pause")
        self.gps.stop()
        return True

    def on_resume(self):
        Logger.info("VigiCamera on_resume")
        self.gps.restart()


    @mainthread
    def on_location(self, **kwargs):
        try:
            p = self.gps.location(**kwargs)
            if p:
                self.lat, self.lon, self.alt = float(p.get('lat')), float(p.get('lon')), float(p.get('altitude'))
                #Logger.info(f'{self.lat} {self.lon}')
                return
        except Exception as e:
            Logger.error(f'GPS on_location error {e}')
        self.lat, self.lon, self.alt = None, None, None

    @mainthread
    def on_status(self, stype, status):
        if self.gps.is_gps:
            msg = f'type={stype}, status={status}'
            Logger.info(msg)


VigiCamera().run()
#
