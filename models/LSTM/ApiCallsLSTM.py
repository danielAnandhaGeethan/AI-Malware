"@Author: NavinKumarMNK"
# Add the parent directory to the path
import sys
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))


# Import the required modules
import torch
import torch.nn as nn
import torch.nn.functional as F
import pytorch_lightning as pl
import torchmetrics
import tensorrt as trt
from models.LSTM.ApiCallsDataset import ApiCallsDataModule
import ray_lightning as rl
import utils.utils as utils

class SystemCallLSTM(pl.LightningModule):
    def __init__(self, num_classes:int=2, input_size:int=102, hidden_size:int=256, 
                    num_layers:int=2, max_length:int=1000) -> None:
        super().__init__()
        self.file_path = utils.ROOT_PATH + '/weights/apicall_lstm'
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.input_size = input_size
        self.max_length = max_length
        self.example_input_array = torch.rand(1, self.max_length, self.input_size)
        self.example_output_array = torch.rand(1, num_classes)
        self.lstm = nn.LSTM(input_size=self.input_size, hidden_size=hidden_size, num_layers=num_layers, batch_first=True)
        # pad the sequence to max_length input size (batchsize, any_length, 102)
        self.best_val_loss = None
        self.fc1 = nn.Linear(hidden_size, int(hidden_size / 4))
        self.fc2 = nn.Linear(int(hidden_size / 4), int(hidden_size / 16))
        self.fc3 = nn.Linear(int(hidden_size / 16), num_classes)
        
        self.save_hyperparameters()
        try:
            self.lstm = torch.load(utils.ROOT_PATH + '/weights/apicall_lstm.pt')
        except FileNotFoundError:
            torch.save(self.lstm, utils.ROOT_PATH + '/weights/apicall_lstm.pt')

    def forward(self, x):
        # x.shape: (batch_size, seq_size, input_size)
        out, _ = self.lstm(x)
        out = self.fc3(self.fc2(self.fc1(out[:, -1, :]))) # only use the last timestep
        return out
    
    def configure_optimizers(self):
        optimizer = torch.optim.Adam(self.parameters(), lr=0.001)
        return optimizer
    
    def training_step(self, batch, batch_idx):
        x, y = batch
        print(x.shape)
        y_hat= self(x)
        loss = nn.CrossEntropyLoss()(y_hat, y)
        self.log('train/loss', loss)
        return loss

    def training_epoch_end(self, outputs):
        avg_loss = torch.stack([x['loss'] for x in outputs]).mean()
        self.log('train/loss', avg_loss)
    
    def validation_step(self, batch, batch_idx):
        x, y = batch
        print(x.shape)
        y_hat = self(x)
        loss = F.cross_entropy(y_hat, y)
        self.log('val/loss', loss)
        acc = (y_hat.argmax(dim=1) == y).float().mean()
        self.log('val/acc', acc)
        return {'val_loss': loss, 'val_acc': acc}
    
    def validation_epoch_end(self, outputs):
            print(outputs[0])
            avg_loss = torch.stack([x['val_loss'] for x in outputs]).mean()
            avg_acc = torch.stack([x['val_acc'] for x in outputs]).mean()
            self.log('val/loss', avg_loss)
            self.log('val/acc', avg_acc, prog_bar=True)
            if(self.best_val_loss) == None:
                self.best_val_loss = avg_loss
                #self.save_model()
            elif (avg_loss < self.best_val_loss):
                self.best_val_loss = avg_loss
                self.save_model()

    def save_model(self):
        torch.save(self.lstm,  utils.ROOT_PATH + '/weights/apicall_lstm.pt')
        artifact = wandb.Artifact('SystemCallClassifier.cpkt', type='model')

    def test_step(self, batch, batch_idx):
        x, y = batch
        y_hat = self(x)
        loss = F.cross_entropy(y_hat, y)
        self.log('test/loss', loss)
        self.log('test/acc', torchmetrics.functional.accuracy(y_hat, y))
        return loss

    def finalize(self):
        self.save_model()
        self.to_onnx(self.file_path+'.onnx', self.example_input_array, export_params=True)
        self.to_torchscript(self.file_path+'_script.pt', method='script')
        self.to_tensorrt()

    def to_tensorrt(self):
        TRT_LOGGER = trt.Logger(trt.Logger.WARNING)
        with trt.Builder(TRT_LOGGER) as builder, builder.create_network(1 << int(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH)) as network, trt.OnnxParser(network, TRT_LOGGER) as parser:
            builder.max_batch_size = 1
            with open(self.file_path+'.onnx', 'rb') as model:
                parser.parse(model.read())
            
            config = builder.create_builder_config()
            config.set_memory_pool_limit(trt.MemoryPoolType.WORKSPACE, 1024*1024*1024)
            config.set_flag(trt.BuilderFlag.FP16)

            network.get_input(0).shape = [1000, 102]
            engine = builder.build_serialized_network(network, config)
            engine = builder.build_engine(network, config)
            with open(self.file_path+'.trt', 'wb') as f:
                f.write(engine.serialize()) 

if __name__ == '__main__': 
    from pytorch_lightning.loggers import WandbLogger
    logger = WandbLogger(project='Malware-Analysis', name='Api-Call-LSTM')

    import wandb
    wandb.init()
    from pytorch_lightning import Trainer
    from torch.utils.data import DataLoader

    #import ray
    #ray.init(runtime_env={"working_dir": utils.ROOT_PATH},
    #         )


    dataset_params = utils.config_parse('APICALLS_DATASET')
    print(dataset_params)
    dataset = ApiCallsDataModule(
        batch_size=dataset_params['batch_size'],
        num_workers=dataset_params['num_workers'],
        annotation=dataset_params['annotation'],
        data_dir_path=dataset_params['data_dir_path'],
    )
    dataset.setup()

    from pytorch_lightning.callbacks import ModelSummary
    from pytorch_lightning.callbacks.progress import TQDMProgressBar
    from pytorch_lightning.callbacks import ModelCheckpoint
    from pytorch_lightning.callbacks import EarlyStopping
    from pytorch_lightning.callbacks.device_stats_monitor import DeviceStatsMonitor

    early_stopping = EarlyStopping(monitor='val/loss', patience=5)
    device_monitor = DeviceStatsMonitor()
    checkpoint_callback = ModelCheckpoint(dirpath=utils.ROOT_PATH + '/weights/checkpoints/malcoatnet/',
                                            monitor="val/loss", mode='min', every_n_train_steps=50, save_top_k=1, save_last=True)
    model_summary = ModelSummary(max_depth=5)
    refresh_rate = TQDMProgressBar(refresh_rate=10)

    callbacks = [
        model_summary,
        refresh_rate,
        checkpoint_callback,
        early_stopping,
        device_monitor
    ]

    api_lstm = utils.config_parse('SYSTEMCALL_LSTM')
    
    model = SystemCallLSTM(**api_lstm)
    syscall_params = utils.config_parse('APICALLS_TRAIN')
    
    dist_env_params = utils.config_parse('DISTRIBUTED_ENV')
    strategy = None
    if int(dist_env_params['horovod']) == 1:
        strategy = rl.HorovodRayStrategy(num_workers=dist_env_params['num_workers'],
                                        use_gpu=dist_env_params['use_gpu'])
    elif int(dist_env_params['model_parallel']) == 1:
        strategy = rl.RayShardedStrategy(num_workers=dist_env_params['num_workers'],
                                        use_gpu=dist_env_params['use_gpu'])
    elif int(dist_env_params['data_parallel']) == 1:
        strategy = rl.RayStrategy(num_workers=dist_env_params['num_workers'],
                                        use_gpu=dist_env_params['use_gpu'])
    trainer = Trainer(**syscall_params, 
                    callbacks=callbacks, 
                    logger=logger,
                    #strategy=strategy,
                    log_every_n_steps=5)
    

    trainer.fit(model, dataset)
    model.save_model()
    
    #model.finalize()

    trainer.test(model, dataset.test_dataloader())
    wandb.finish()    
    model.finalize()

    