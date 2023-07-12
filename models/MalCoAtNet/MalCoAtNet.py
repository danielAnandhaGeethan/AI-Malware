'@Author:NavinKumarMNK'
import torch

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from torch import nn
import pytorch_lightning as pl
from models.MalCoAtNet.CoAtNet import CoAtNet
from models.MalCoAtNet.SVM import SVM
import utils.utils as utils
import tensorrt as trt


class MalCoAtNet(pl.LightningModule):
    def __init__(self, weights_path, in_channels=3):
        super(MalCoAtNet, self).__init__()
        self.model = CoAtNet(in_channels=in_channels)
        self.weights_path = weights_path
        self.example_input_array = torch.randn(1, in_channels, 256, 256)
        self.example_output_array = torch.randn(1, 1536)
        self.save_hyperparameters()
        self.best_val_loss = None
        try:
            print(utils.ROOT_PATH + self.weights_path + '.pt')
            self.model = torch.load(utils.ROOT_PATH + self.weights_path + '.pt')
        except FileNotFoundError:
            torch.save(self.model, utils.ROOT_PATH + self.weights_path + '.pt')
        
    def forward(self, x):
        x = self.model(x)
        return x

    def feature_extractor(self, x):
        x = self.model(x)
        return x

    @torch.jit.export
    def predict_step(self, batch, batch_idx):
        x1 = self.model(batch)
        x2 = SVM(x1)
        return x1, x2

    def save_model(self):
        torch.save(self.model, utils.ROOT_PATH + self.weights_path + '.pt')
        
    def count_parameters(self):
        return sum(p.numel() for p in self.parameters() if p.requires_grad)
    
    def finalize(self):
        self.save_model()
        #self.to_torchscript(utils.ROOT_PATH + self.weights_path +"_script.pt", method="script", example_inputs=self.example_input_array)         
        self.to_onnx(utils.ROOT_PATH + self.weights_path +"_onnx.onnx", self.example_input_array, export_params=True)
        self.to_tensorrt()        

    def to_tensorrt(self):
        TRT_LOGGER = trt.Logger(trt.Logger.WARNING)
        with trt.Builder(TRT_LOGGER) as builder, builder.create_network(1 << int(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH)) as network, trt.OnnxParser(network, TRT_LOGGER) as parser:
            builder.max_batch_size = 1
            with open(utils.ROOT_PATH + self.weights_path+'_onnx.onnx', 'rb') as model:
                parser.parse(model.read())
            
            config = builder.create_builder_config()
            config.set_memory_pool_limit(trt.MemoryPoolType.WORKSPACE, 1024*1024*1024)
            config.set_flag(trt.BuilderFlag.FP16)

            network.get_input(0).shape = self.example_input_array.shape
            engine = builder.build_serialized_network(network, config)
            engine = builder.build_engine(network, config)
            with open(utils.ROOT_PATH + self.weights_path+'.trt', 'wb') as f:
                f.write(engine.serialize()) 
    
if __name__ == '__main__':
    model = MalCoAtNet('/weights/MalCoAtNet')
    print(model.count_parameters())
    model.finalize()
