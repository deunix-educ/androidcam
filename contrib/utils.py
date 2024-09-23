'''
Created on 20 avr. 2022

@author: denis
'''
import datetime, string, secrets, yaml, uuid
from decimal import Decimal

def yaml_load(f):
    with open(f, 'r') as stream:
        return yaml.safe_load(stream)
    return {}

def yaml_save(f, context):
    with open(f, 'w') as stream:
        yaml.dump(context, stream, default_flow_style = False)

def bitread(b, bitpos):
    return (b>>bitpos) & 0x1

def get_uuid():
    return str(hex(uuid.getnode()))[2:]

def ts_now(m=1):
    now = datetime.datetime.now().timestamp()*m
    return int(now)

def random_num(n=16):
    alphabet = string.digits
    return ''.join(secrets.choice(alphabet) for i in range(n))  # @UnusedVariable

def random_chars(n=6):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(n))  # @UnusedVariable

def get_apikey(n=32):
    chars = 'abcdefghijklABCDEFGHIJKLmnopqrstuvwxyz0123456789MNOPQRSTUVWXYZ'
    return ''.join(secrets.choice(chars) for i in range(n))  # @UnusedVariable

def str_to_float(n, default='NaN'):
    try:
        return float(str(n).strip().replace(',', '.'))
    except:
        return default

def str_to_int(n, default='NaN'):
    try:
        return int(str(n).strip())
    except:
        return default

def gps_conv(s, n=1000000):
    try:
        return str(Decimal(s)*n)
    except:
        return 'NaN'

def gen_device_uuid(n=19):
    return hex(int(random_num(n)))[2:]

def get_device_uuid(n=19):
    return f'0x{gen_device_uuid(n)}'

def dimensions(s):
    w, h = s.split('x')
    return int(w), int(h)

def dim_to_size(w, h):
    return f'{w}x{h}'
