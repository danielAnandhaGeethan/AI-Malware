import lightgbm as lgb
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import utils.utils as utils
import pickle
from etl.lief_feature import PEFeatureExtractor
import json

class LGBMPredictor():
    def __init__(self):
        self.model = lgb.Booster(model_file=utils.ROOT_PATH + "/weights/lightgbm.model")
        with open(utils.ROOT_PATH + '/weights/lgb_model.pkl', 'wb') as f:
            pickle.dump(self.model, f)
        
        self.pe = PEFeatureExtractor()
            
    def predict(self, hash, file_type):
        if file_type == 'exe':
            f = utils.TEMP_PATH + f"/malware/{file_type}/" + hash + '.exe'
        else:
            f = utils.TEMP_PATH + f"/malware/{file_type}/" + hash + '.apk'
        f = open(f, 'rb')
        feat = self.pe.feature_vector(f.read())
        save = feat.tolist()
        # save the feature vector as json
        with open(utils.TEMP_PATH + f"/sf/" + hash + '.json', 'w') as f:
            json.dump(save, f)

        return self.model.predict(feat.reshape(1, -1))

if __name__ == '__main__':
    lgbm = LGBMPredictor(utils.ROOT_PATH + "/weights/lightgbm.model")
    print(lgbm.predict('putty', 'exe'))