'''
class for torch models that can be regressors to the negative log-likelihood 
'''

import torch
from torch import nn
import numpy as np 

class Model(nn.Module):
    '''
    regressor network, can later be modified to fit any idea we might come up with
    '''
    def __init__(self, input_size, n_hidden):
        super().__init__()
        self.layers = nn.Sequential(
                nn.Linear(input_size, n_hidden),
                nn.ReLU(),
                nn.Linear(n_hidden, n_hidden),
                nn.ReLU(),
                nn.Linear(n_hidden,1)
        )
    def forward(self, x):
        return self.layers(x)


class Dataset(torch.utils.data.Dataset):
  'Characterizes a dataset for PyTorch'
  def __init__(self, xs, ys):
        'Initialization'
        self.ys = ys
        self.xs = xs

  def __len__(self):
        'Denotes the total number of samples'
        return len(self.xs)

  def __getitem__(self, index):
        'Generates one sample of data'
        # Select sample
        ID = self.xs[index]

        # Load data and get label
        X = self.xs[index]
        y = self.ys[index]

        return X, y


class Trainer():
     '''
     training instance that holds dataset, training and trained model 
     '''
     def __init__(self, model, dataset, lossfunction):
          self.model = model
          self.dataset = dataset
          self.loss = lossfunction
    
    def train(n_epoch, lr):
        '''
        trains the model
        '''
        optim = torch.optim.Adam(self.model.parameters(), lr=lr)
        trainload = torch.util.DataLoader(self.dataset, batch_size=128, shuffle= True)
        print(f' model is on GPU: {next(mlp.parameters()).is_cuda}')
        for epoch in range(0, n_epoch):
            print(f'Starting epoch {epoch+1}')
            # Set current loss value
            current_loss = 0.0
            # Iterate over the DataLoader for training data
            i = 0
            for data in iter(trainload):
                # Get inputs
                inputs, targets = data
                # Zero the gradients
                optimizer.zero_grad()
                # Perform forward pass
                outputs = self.model(inputs.float())
                # Compute loss
                loss = self.loss(outputs.float(), targets.float())
                # Perform backward pass
                loss.mean().backward()
                # Perform optimization
                optimizer.step()
                # Print statistics
                current_loss += loss.mean().item()
                i = i+1
            print(f'loss is {loss.mean()} after epoch {epoch}')
        print(f' training finished with a loss of: {current_loss}')
                                                               