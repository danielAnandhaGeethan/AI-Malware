import configparser
import os
import hashlib
    

def current_path():
    return os.path.abspath('./')

ROOT_PATH = '/home/mnk/MegNav/Projects/AI-Malware-System'
TEMP_PATH = '/home/mnk/MegNav/Projects/AI-Malware-System/temp'
def absolute_path(txt):
        return os.path.join(ROOT_PATH, txt)

# Congifuration file
def config_parse(txt):
    config = configparser.ConfigParser()
    
    path = './config.cfg'
    config.read(path)
    params={}
    try:
        for key, value in config[txt].items():
            if 'path' in key.split('_'):
                params[key] = absolute_path(value)
            elif value == 'True' or value== 'False':
                params[key] = True if value == 'True' else False
            elif value.isdigit():
                params[key] = int(value)
            elif '.' in value:
                try:
                    params[key] = float(value)
                except ValueError:
                    params[key] = value
            else:
                params[key] = value
    except KeyError as e:
        print("Invalid key: ", e)
        print(path)    
    
    return params


#random filename using uuid that resembles like hash & data and time
def sha256_file(data):
    sha = hashlib.sha256()
    sha.update(data)
    hash = sha.hexdigest()
    return hash

    