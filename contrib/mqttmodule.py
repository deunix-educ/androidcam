#
#
from kivy.logger import Logger, LOG_LEVELS
from threading import Event, Thread
import plyer  # @UnusedImport
import json
from . import utils
from . import mqttc


Logger.setLevel(LOG_LEVELS["info"])

TOPIC_KEYS = {
    'org': 0, 'uuid': 1, 'evt': 2, 'action': 3, 'ts': 3, 'counter': 4, 'lat': 5, 'lon': 6, 'fps': 7,
}

class Topics:

    def __init__(self, topics):
        self.topic_keys = TOPIC_KEYS
        self.topics = topics.split('/') or None

    def is_values(self):
        return self.topics is not None

    def val(self, k):
        return self.topics[self.topic_keys.get(k)]


class VigiCamDaemon(mqttc.MqttBase):

    def __init__(self, parent, configfile, settings, config):
        self.parent = parent
        self.conf_file = configfile
        self.settings = settings
        self.config = config
        mqttconf = settings.get(self.config.get('mqtt'))
        uuid = self.get_uuid(self.config.get('uuid'))
        topic_base = self.config.get('topic_base')
        topic_subs = self.config.get('topic_subs')
        super().__init__(uuid=uuid, topic_base=topic_base, topic_subs=topic_subs, **mqttconf)
        self.record = self.config.get('record')
        self.play = self.parent.playing
        self.sleeping = False
        
    def get_uuid(self, uuid):
        if not self.config.get('uuid'):
            uuid = f'0x{utils.gen_device_uuid()}'
            org = self.config['org']
            self.config['uuid'] = uuid
            self.config['topic_base'] = f"{org}/{uuid}"
            self.config['topic_subs']= [ [f"{org}/{uuid}/set/#", 0], ]
            self.save_config()
        return uuid

        
    def start_services(self):
        Logger.info(f"Start service")
        self.startMQTT()


    def stop_services(self):
        Logger.info(f"Stop service")
        #self.publish('kill', sid=self.uuid)
        self.stopMQTT()


    def save_config(self):
        utils.yaml_save(self.conf_file, self.settings)
        Logger.info(f"Save config record: {self.record}")


    def save_record(self, payload):
        self.record = self.config['record'] = int(payload.get('record', 0))
        self.save_config()
        
    def save_configuration(self, payload):
        try:     
            self.config['rotate'] = int(payload.get('rotate', 0))
            self.config['fps'] = int(payload.get('fps', 5))
            self.config['zoom'] = float(payload.get('zoom', 0.5))
            self.config['mqtt'] = payload.get('mqtt', 'private')  
            self.save_record(payload)
        except Exception as e:
            Logger.error(f"VigiCamDaemon::save_configuration: {e}")
            

    def publish(self, evt, **payload):
        if self.topic_base:
            topic = f'{self.topic_base}/{evt}'
            Logger.info(f"Device publish {topic}")
            self._publish_message(topic, **payload)


    def publish_bytes(self, videotopic, frame):
        topic = f"{self.topic_base}/jpg/{utils.ts_now(m=1000)}/{videotopic}"
        self._publish_bytes(topic.replace(' ', ''), frame)


    def get_state(self, state):
        return 'play' if state else 'pause'


    def is_alive(self, timeout=5.0):
        Event().wait(timeout)
        if (self.pong_time-self.ping_time) < 0:
            if not self.record:
                #self.play = False
                self.parent.playing = False
                Logger.info(f'Mobile is not alive for {self.uuid}')
                self.sleeping = True
                self.publish('report', retain=True, **self.makeReport())
                

    def makeReport(self):
        return dict(
            name=self.config.get('title'),
            sensor=self.config.get('sensor'),
            vendor=self.config.get('vendor'),
            model_id=self.config.get('model_id'),
            description=self.config.get('description'),
            org=self.config.get('org'),  
            uuid=self.uuid,
            ip=self.config.get('ip'),
            service="",
            record=self.record,         
            options = json.dumps(dict(
                lat=float(self.config.get('lat')),
                lon=float(self.config.get('lon')),
                rotate=int(self.config.get('rotate')),
                contour=0,
                record=self.record, 
                zoom=float(self.config.get('zoom')),
                fps=int(self.config.get('fps')),
                mqtt=self.config.get('mqtt'),
                state=self.get_state(self.parent.playing),
                sleeping=self.sleeping,
                mobile=self.config.get('mobile'),
                )
            ),
        )

    def _on_log(self, mqttc, obj, level, string):  # @UnusedVariable
        try:
            if 'PINGRESP' in string:
                self.pong_time, self.ping_time = 0, utils.ts_now(m=1000)
                self.publish('ping', ts=self.ping_time, **self.makeReport())
                Logger.info(f"ping ts={self.ping_time}")
                timer = Thread(target=self.is_alive, args=(5.0, ))
                timer.start()
                
        except Exception as e:
            Logger.error(f"On log error {e}")


    def _on_connect_info(self, info):
        self.parent.wait_for_mqtt.set() # cancel timer
        Logger.info(info)   
        self.sleeping = False
        self.publish('report', retain=True, **self.makeReport())
        

    def _on_message_callback(self, topic, payload):
        Logger.info(f"On message callback >> {topic} {payload}")
        topics = Topics(topic)
        evt = topics.val('evt')
        if evt=='set':
            action = topics.val('action')
            if action:
                if action == 'pause':
                    Logger.info(f"Pause video {self.uuid}")
                    self.parent.playing = False
                elif action == 'play':
                    Logger.info(f"Play video {self.uuid}")
                    self.parent.playing = True
                elif action == 'toggle':
                    self.parent.playing = False if self.parent.playing else True
                    Logger.info(f"Video=={self.play} {self.uuid}")
                    
                elif action == 'save':
                    self.save_configuration(payload)
                    Logger.info(f"Save config {self.uuid}: {payload}")
                self.sleeping = False
                self.publish('report', retain=True, **self.makeReport())
        elif evt=='rec':
            self.save_config(payload)
            self.sleeping = False
            self.publish('report', retain=True, sleeping=False, **self.makeReport())
        elif evt=='pong':
            self.pong_time = payload.get('ts')
       
