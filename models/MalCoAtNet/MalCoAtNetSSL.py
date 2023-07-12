'@Author: NavinKumarMNK'
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
import utils.utils as utils

import torch
import torch.nn as nn
import torch.nn.functional as F
import pytorch_lightning as pl
import tensorrt as trt
import wandb
from models.MalCoAtNet.MalCoAtNet import MalCoAtNet
from models.MalCoAtNet.MalCoAtNetPreTrain import MalCoAtNetSSLDataModule

class MalCoAtNetSSL(pl.LightningModule):
    def __init__(self, projection_dim=1536, temperature=0.5, in_channels=3):
        super().__init__()
        self.model = MalCoAtNet(in_channels=in_channels)
        self.output_dim = 1536
        self.projection_dim = projection_dim
        self.temperature = temperature

        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        if in_channels == 3:
            self.data_type = 'RGB'
        elif in_channels == 2:
            self.data_type = 'BB'
        
        self.save_hyperparameters()
        self.example_input_array = torch.randn(1, in_channels, 256, 256)
        self.example_output_array = torch.randn(1, 1536)
        self.proj_head = nn.Sequential(
            nn.Linear(self.output_dim, self.output_dim),
            nn.ReLU(inplace=True),
            nn.Linear(self.output_dim, projection_dim),
        )

        self.best_val_loss = None
        if in_channels == 3:
            self.weights_path = 'weights/MalCoAtNet/MalCoAtNetSimCLR_RGB'
        else :
            self.weights_path = 'weights/MalCoAtNet/MalCoAtNetSimCLR_BB'

        try:
            print(utils.ROOT_PATH + self.weights_path + '.pt')
            self.model = torch.load(utils.ROOT_PATH + self.weights_path + '.pt')
        except FileNotFoundError:
            torch.save(self.model, utils.ROOT_PATH + self.weights_path + '.pt')

        try:
            print(utils.ROOT_PATH + self.weights_path + '_proj_head.pt')
            self.proj_head = torch.load(utils.ROOT_PATH + self.weights_path + '_proj_head.pt')
        except FileNotFoundError:
            torch.save(self.proj_head, utils.ROOT_PATH + self.weights_path + '_proj_head.pt')

    def forward(self, x):
        x = self.model(x)
        h = x.view(x.size(0), -1)
        z = self.proj_head(h)
        return F.normalize(z, dim=1)
    
    def combined_loss(self, z_i: torch.Tensor, z_j: torch.Tensor, labels: torch.Tensor, temperature: float = 0.5) -> torch.Tensor:
        """
        Combined SimCLR and contrastive loss.
        """
        # compute similarity scores
        sim_i_j = torch.matmul(z_i, z_j.T) / temperature
        sim_j_i = torch.matmul(z_j, z_i.T) / temperature

        # create positive and negative masks
        pos_mask = (labels.unsqueeze(1) == labels.unsqueeze(0))
        neg_mask = ~pos_mask


        # compute positive and negative similarity scores
        pos_sim = torch.cat((sim_i_j[pos_mask], sim_j_i[pos_mask]))
        neg_sim = torch.cat((sim_i_j[neg_mask], sim_j_i[neg_mask]))

        # compute SimCLR loss
        numerator = torch.exp(pos_sim)
        denominator = torch.sum(torch.exp(neg_sim), dim=0)
        simclr_loss = -torch.log(numerator / denominator).mean()

        # compute contrastive loss
        margin = 1.0
        pos_pair_idx = (labels.unsqueeze(1) == labels.unsqueeze(0)).nonzero(as_tuple=False)
        neg_pair_idx = (labels.unsqueeze(1) != labels.unsqueeze(0)).nonzero(as_tuple=False)
        pos_pair_sim = sim_i_j[pos_pair_idx[:, 0], pos_pair_idx[:, 1]]
        neg_pair_sim = sim_i_j[neg_pair_idx[:, 0], neg_pair_idx[:, 1]]
        contrastive_loss = torch.mean(torch.clamp(margin - pos_pair_sim + neg_pair_sim, min=0))
        
        loss = simclr_loss + contrastive_loss
        self.log("simclr_loss", simclr_loss)
        self.log("contrastive_loss", contrastive_loss)
        self.log('train_loss', loss)

        return loss

    def training_step(self, batch, batch_idx):
        x_i, x_j, labels = batch
        z_i, z_j = self(x_i), self(x_j)
        loss = self.combined_loss(z_i, z_j, labels, self.temperature)
        self.log('train_loss', loss, prog_bar=True)
        return loss
    
    def training_epoch_end(self, outputs):
        avg_loss = torch.stack([x['loss'] for x in outputs]).mean()
        self.log('train/loss', avg_loss)

    def validation_step(self, batch, batch_idx):
        x_i, x_j, labels = batch
        z_i, z_j = self(x_i), self(x_j)
        combined_loss = self.combined_loss(z_i, z_j, labels, self.temperature)
        self.log('val_loss', combined_loss, prog_bar=True)
        return {"val_loss": combined_loss}

    def validation_epoch_end(self, outputs):
        avg_loss = torch.stack([x['val_loss'] for x in outputs]).mean()
        self.log('val/loss', avg_loss, prog_bar=True)
        if self.best_val_loss is None or avg_loss < self.best_val_loss:
            self.best_val_loss = avg_loss
            self.save_model()

    def configure_optimizers(self):
        optimizer = torch.optim.Adam(self.parameters(), lr=3e-4)
        return optimizer
        
    def test_step(self, batch, batch_idx):
        x_i, x_j, labels = batch
        z_i, z_j = self(x_i), self(x_j)
        combined_loss = self.combined_loss(z_i, z_j, labels, self.temperature)
        self.log('test_loss', combined_loss, prog_bar=True)
        return {"test_loss": combined_loss}
    
    def test_epoch_end(self, outputs):
        avg_loss = torch.stack([x['test_loss'] for x in outputs]).mean()
        self.log('test/loss', avg_loss)

    def save_model(self):
        torch.save(self.model, utils.ROOT_PATH + self.weights_path + '.pt')
        torch.save(self.proj_head, utils.ROOT_PATH + self.weights_path + '_proj_head.pt')
        
    def count_parameters(self):
        return sum(p.numel() for p in self.parameters() if p.requires_grad)
    

def train():
    #import ray
    # #ray.init(runtime_env={"working_dir": utils.ROOT_PATH},
    #         )
    dataset_params = utils.config_parse('MALBINIMG_BB_DATASET')  
    dataset = MalCoAtNetSSLDataModule(**dataset_params)
    dataset.setup() 
    print("dataset complete")

    from pytorch_lightning.callbacks import ModelSummary
    from pytorch_lightning.callbacks.progress import TQDMProgressBar
    from pytorch_lightning.callbacks import ModelCheckpoint
    from pytorch_lightning.callbacks import EarlyStopping
    from pytorch_lightning.callbacks.device_stats_monitor import DeviceStatsMonitor

    import ray_lightning as rl

    early_stopping = EarlyStopping(monitor='val/loss', patience=5)
    device_monitor = DeviceStatsMonitor()
    checkpoint_callback = ModelCheckpoint(dirpath=utils.ROOT_PATH + '/weights/checkpoints/malcoatnet/',
                                            monitor="val/loss", mode='min', every_n_train_steps=100, save_top_k=5, save_last=True)
    checkpoint_callback2 = ModelCheckpoint(dirpath=utils.ROOT_PATH + '/weights/checkpoints/malcoatnet2/', 
                                            every_n_epochs=10, save_top_k=2, save_last=True) 
    model_summary = ModelSummary(max_depth=5)
    refresh_rate = TQDMProgressBar(refresh_rate=10)


    callbacks = [
        model_summary,
        refresh_rate,
        checkpoint_callback,
        early_stopping,
        device_monitor,
        checkpoint_callback2
    ]

    mal_clf = utils.config_parse('MALWARE_CLASSIFIER_BB')
    model = MalCoAtNetSSL(**mal_clf)
    mal_clf_params = utils.config_parse('MALWARE_CLASSIFIER_TRAIN')


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
    
    trainer = Trainer(**mal_clf_params, 
                    callbacks=callbacks,
                    logger=logger,
		    accelerator='gpu',
                    #strategy='deepspeed_stage_1',
		    #num_nodes=4,
            log_every_n_steps=5,
            #resume_from_checkpoint=utils.ROOT_PATH + '/weights/checkpoints/malcoatnet/last.ckpt',
                    )

    trainer.fit(model, dataset)
        
    
    #model.save_model()

    #model.model.finalize()

    #trainer.test(model, dataset.test_dataloader())
    wandb.finish()

    
    '''
    # SVM Data Preparation
    # inference of model
    model.model.eval()
    features = []
    for batch in dataset.train_dataloader():
        y = model.model.feature_extractor(batch[0])
        y = y.view(y.size(0), -1)
        label = batch[1]
        # combine y and label
        y = torch.cat((y, label.unsqueeze(1)), dim=1)
        features.append(y)
    '''




if __name__ == "__main__":
    model = MalCoAtNetSSL(in_channels=3, output_dim=128, projection_dim=128)
    print(model.count_parameters())

    wandb.init()
    from pytorch_lightning.loggers import WandbLogger
    from pytorch_lightning import Trainer
    logger = WandbLogger(project='Malware-Analysis', name='Malware Classifer')

    train()
