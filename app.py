"@author: NavinKumarMNK"
from fastapi import FastAPI, UploadFile, File
import uvicorn
import utils.utils as utils
import json
import os
from PIL import Image
import requests
import Azure.blob_data_injestion as blob
import Azure.sql_data_injestion as sql

params = utils.config_parse('PRODUCTION')

"""
@files :
    temp/malware/<uhash>.exe
    temp/cuckoo/<uhash>.json
    temp/img/<uhash>.json
    temp/report/<uhash>.json
    temp/sf/<uhash>.json
"""

'''
if params['production'] == 1:
    try:
        from azure.eventhub import EventHubProducerClient, EventData
    except ImportError as e:
        print(e)
        exit(1)

    CONNECTION_STRING = params['connection_string']
    EVENTHUB_NAME = params['eventhub_name']

    producer_client = EventHubProducerClient.from_connection_string(
        conn_str=CONNECTION_STRING, eventhub_name=EVENTHUB_NAME)
    
    @brief : send 3 json files and separate exe file which were not realted
                send malware, json files
                send the batch of events to the event hub.

    async def send_to_hub(file_name):
        try:
            with producer_client:
                event_data_batch = producer_client.create_batch()
                if os.path.exists(utils.ROOT_PATH + params['temp_data_path'] + 'malware/and' + file_name):
                    event_data_batch.add(EventData(utils.ROOT_PATH + params['temp_data_path'] + 'malware/win' + file_name))
                if os.path.exists(utils.ROOT_PATH + params['temp_data_path'] + 'malware/win' + file_name):
                    event_data_batch.add(EventData(utils.ROOT_PATH + params['temp_data_path'] + 'malware/win' + file_name))
                if os.path.exists(utils.ROOT_PATH + params['temp_data_path'] + 'json/' + file_name + '.json'):
                    event_data_batch.add(EventData(utils.ROOT_PATH + params['temp_data_path'] + 'json/' + file_name + '.json'))
                if os.path.exists(utils.ROOT_PATH + params['temp_data_path'] + 'img/' + file_name + '_dex.json'):
                    event_data_batch.add(EventData(utils.ROOT_PATH + params['temp_data_path'] + 'image/' + file_name + '_dex.png'))
                if os.path.exists(utils.ROOT_PATH + params['temp_data_path'] + 'img/' + file_name + '_dex.json'):
                    event_data_batch.add(EventData(utils.ROOT_PATH + params['temp_data_path'] + 'image/' + file_name + '_win.png'))
                if os.path.exists(utils.ROOT_PATH + params['temp_data_path'] + 'report/' + file_name + '.json'):
                    event_data_batch.add(EventData(utils.ROOT_PATH + params['temp_data_path'] + 'report/' + file_name + '.json'))
                if os.path.exists(utils.ROOT_PATH + params['temp_data_path'] + 'sf/' + file_name + '.json'):
                    event_data_batch.add(EventData(utils.ROOT_PATH + params['temp_data_path'] + 'sf/' + file_name + '.json'))
                
                producer_client.send_batch(event_data_batch)
                print("A batch of {} events has been published.".format(len(file_name)))
        except Exception as e:
            print(e)
'''

async def coatnet_inference(file_path:str, method=1):
    filename = file_path.split('/')[-1].split('.')[0]
    file_ext = file_path.split('/')[-1].split('.')[1]
    import torchvision.transforms as transforms
    import torch
    
    if method == 1:
        if file_ext == "apk":
            from etl.AndroMal2Img import create_linear_image as create_image
            save_img = utils.TEMP_PATH + '/image/RGB/' + filename + ".png"
        elif file_ext == "exe":
            from etl.WindMal2Img import create_linear_image as create_image
            save_img = utils.TEMP_PATH + '/image/RGB/' + filename + ".png"
        transform = transforms.Compose([
            transforms.Resize((256, 256)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])    

    elif method == 2:
        from etl.Mal2ImgBB import get_mal2img_bb as create_image
        save_img = utils.TEMP_PATH + '/image/BB/' + filename + ".png"
        transform = transforms.Compose([
            transforms.Resize((256, 256)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.5, 0.5], std=[0.5, 0.5])
            ])    


    create_image(file_path) 
     
    x = Image.open(save_img)
    params = utils.config_parse('MALWARE_CLASSIFIER_RGB')
    i=1
    if i==0:
        from models.MalCoAtNet.SVM import SVM
        from models.MalCoAtNet.MalCoAtNet import MalCoAtNet
        feature_extractor = MalCoAtNet(weights_path=params['weights_path'],
                                       in_channels=params['in_channels']) 
        feature_extractor.eval()
        with torch.no_grad():    
            x = transform(x)
            feature = feature_extractor(x)
            classifier = SVM()
            y = classifier.predict(feature)
            
    else:
        from models.MalCoAtNet.RGB.MalwareClassifer import MalwareClassifer
        model = MalwareClassifer(**params)
        model.eval()
        with torch.no_grad():
            x = transform(x)
            x = x.unsqueeze(0)
            y = model(x)

    probs = torch.softmax(y, dim=1)
    probs = probs[0, 1]
    probs = probs.detach().numpy().tolist()
    print(probs)
    return probs

async def api_analysis(file_path):
    '''
    import json
    url = "http://localhost:8050/testfile"

    with open(file_path, 'rb') as f:
        files = {'file': f}
        response = await requests.post(url, files=files)
        
    if response.status_code == 200:
        data = response.json()['json_output']
        # save json from json object
        with open(utils.ROOT_PATH + '/temp/cuckoo/' + file_path.split('/')[-1] + '.json', 'w') as f:
            json.dump(data, f)    
            
    else:
        print(f"Error: {response.status_code} ({response.reason})") 
    '''

    import torch
    from models.LSTM.ApiCallsLSTM import SystemCallLSTM
    from etl.system_call_features import Cuckoo2DMDS
    obj = Cuckoo2DMDS()
    model = SystemCallLSTM()

    json_file_path = utils.ROOT_PATH + '/temp/cuckoo/' + file_path.split('/')[-1].split('.')[0] + '.json'
    
    output = obj(json_file_path.split('/')[-1].split('.')[0])
    output = torch.tensor(output)
    output = output.unsqueeze(0)

    with torch.no_grad():
        model.cuda()
        model.eval()
        y = model(output.cuda())
        y = torch.softmax(y, dim=1)
        y = y.cpu()
        y = y.detach().numpy().tolist()

    print(y)
    probs = y[0][1]
    print(probs)
    return probs

    

async def server_analysis(file_path):
    from etl.remnux.file2log import analyse
    results = analyse()
    return results

async def lgbm_predict(file_path):
    import lightgbm
    from models.LightGBM.lgbm_predict import LGBMPredictor
    model = LGBMPredictor()
    file_name = file_path.split('/')[-1].split('.')[0]
    file_type = file_path.split('/')[-1].split('.')[1]
    y = model.predict(hash=file_name, file_type=file_type)
    return y

app = FastAPI()

@app.post("/upload")
async def file(file: UploadFile = File(...)):
    """
    @brief : 
        input : File, uploaded by user
        output : json file {predictions, optional message}
    @process :
        > create a unique id for the file
        > save the file to temp/malware/win(or)and/<hash>.exe
        parallel :
            > file2image to MalCoAtNet  
            > file2 cuckoo sandbox & retrieve json 
                > cuckoo.json > api call feature > LSTM
            > file2 lief & retrieve static features json
                > lief.json > LigthGBM
        > make report json
        > send the files, data, json to azure event hub
        > return the results to the user
    """
    
    # malware file to check!
    
    contents = await file.read()
    
    hash = utils.sha256_file(contents)
    file_type = file.filename.split('.')[1]
    file_path = utils.TEMP_PATH + '/malware'
    output_file_name = utils.TEMP_PATH + f"/malware/{file_type}/" + hash + '.exe'
    print(output_file_name)
    with open(output_file_name, 'wb') as f:
        f.write(contents)

    print(file, file.filename)

    if file.filename.split('.')[1] == 'apk':
        from etl.AndroMal2Img import apk2tdex
        file_path += '/apk/' + hash + '.apk'
        apk2tdex(file_path[:-4] + '.apk', file_path + '.dvk')
    elif file.filename.split('.')[1] == 'dvk':
        file_path += '/apk/' + hash + '.dex'
    elif file.filename.split('.')[1] == 'exe':
        file_path += '/exe/' + hash + '.exe'

    else:
        return {'result' : 'not supported file type'}

    x1 = x2 = x3 = x4 = 0
    if params['coatnet'] == 1:
            x1 = await coatnet_inference(file_path=file_path, method=1)
            print("x1", x1)
    if params['api_analysis'] == 1:
            x2 = await api_analysis(file_path=file_path)
            print("x2", x2)
    if params['server_analysis'] == 1:
            x3 = await server_analysis(file_path=file_path)
            print("x3", x3)
    if params['lgbm_classifer'] == 1:
            x4 = await lgbm_predict(file_path=file_path)
            x4 = x4[0]
            print("x4", x4)

    # logic & data sent to respective API
    response = None
    
    '''
    if params['production'] == 1:
        await send_to_hub(file.filename)
    
    #send the contents to azure event hub
    if params['production'] == 1:
        await send_to_hub(file.filename)
    '''

    # azure sql database & blob storage

    response = (x1 + x2 + x3 + x4) / 4
    
    if params['production'] == 1:
        sql_data = [hash +"." +file_type,  x1, x3, x4, x2, "malware"]
        print(sql_data)
        #sql.upload_data_to_sql_database(sql_data)
    if params['production'] == 1:
        #blob.upload_files_to_blob_storage(hash, file_type, 'rgb')
        pass


    response = response / 4 
    print(response)
    return {"result" : response}
    
if __name__ == "__main__":
    import sys
    sys.stdout.write("Initializing...\n")
    import __init__
    __init__.init()
    sys.stdout.write("\033[F") 
    sys.stdout.write("Initialized    \n")

    from fastapi.middleware.cors import CORSMiddleware

    # Configure CORS settings
    origins = [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:1420",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


    uvicorn.run(app, host="localhost", port=8000)