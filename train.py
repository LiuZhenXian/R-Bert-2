import torch
from torch.utils.data import DataLoader, Dataset, RandomSampler
from tqdm import tqdm, trange
import torch.nn as nn

from transformers import *


class Trainer(object):
    def __init__(self, model):
        self.model = model

    def train(self, train_dataset, tokenizer, num_train_epochs=5, lr=2e-5, batch_size=16):
        self.model.train()
        train_sampler = RandomSampler(train_dataset)
        train_dataloader = DataLoader(
            train_dataset, sampler=train_sampler, batch_size=batch_size)
        optimizer = AdamW(self.model.parameters(), lr=lr)
        loss_F = nn.CrossEntropyLoss()
        train_iterator = trange(int(num_train_epochs), desc='Epoch')
        for _ in train_iterator:
            epoch_iterator = tqdm(train_dataloader, desc="Iteration")
            for step, batch in enumerate(epoch_iterator):
                inputs = torch.tensor([i.input_ids for i in batch]).cuda()
                e1_mask = torch.tensor([i.e1_mask for i in batch]).cuda()
                e2_mask = torch.tensor([i.e2_mask for i in batch]).cuda()
                labels = torch.tensor([i.label_id for i in batch]).cuda()
                attention_mask = torch.tensor(
                    [i.attention_mask for i in batch]).cuda()
                outputs = self.model(inputs, attention_mask=attention_mask,
                                     e1_mask=e1_mask, e2_mask=e2_mask)

                loss = loss_F(outputs, labels)

                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

    def get_class(self, x):
        ls = x.tolist()
        index, val = 0, ls[0]
        for i in range(1, len(ls)):
            if val < ls[i]:
                val = ls[i]
                index = i
        return index

    def evalu(self, test_dataset):
        self.model.eval()

        Total = len(test_dataset)
        Right = 0

        input_ids = torch.tensor([x.input_ids for x in test_dataset]).cuda()
        attention_mask = torch.tensor(
            [x.attention_mask for x in test_dataset]).cuda()
        e1_mask = torch.tensor([i.e1_mask for i in test_dataset]).cuda()
        e2_mask = torch.tensor([i.e2_mask for i in test_dataset]).cuda()
        labels = [x.label_id for x in test_dataset]
        predict = self.model(
            input_ids, attention_mask=attention_mask, e1_mask=e1_mask, e2_mask=e2_mask)
        for i in range(len(predict)):
            if self.get_class(predict[i])==labels[i]:
                Right+=1

        print('Accuracy = %f %%, total = %d ' % (Right/Total*100, Total))
