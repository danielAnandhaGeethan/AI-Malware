import utils.utils as utils

def init():
    params = utils.config_parse('PRODUCTION')
    if params['production'] == 1:
        print("Deep Learning Not Attached")
        global necessary_libraries
        import virtualbox
        import pefile
        import sklearn
        import pandas
        import lightgbm
        import androguard
        import sys
        import os
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), './')))
        global necessary_libraries
        neccessary_libraries = {'ligthgbm':lightgbm, 'sklearn':sklearn}
    else:
        print("Deep Learning Attached")
        import torch
        import cv2
        import os
        import sys
        import torch.nn as nn
        import torch.nn.functional as F
        import pytorch_lightning as pl
        sys.path.append(os.path.abspath('../'))
        global necessary_libraries
        neccessary_libraries = {'cv2': cv2, 'torch': torch}

