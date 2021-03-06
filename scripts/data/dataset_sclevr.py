from myutils import *
import h5py
import os.path
import numpy as np
import pandas as pd
import torch
import torch.nn.init
from torch.utils.data import Dataset
from PIL import Image
from torchvision import transforms

class sclevrDataset(Dataset):
    """clevr dataset."""
    def __init__(self, opt, mode = 'train'):
        """
        Args:
            qa_dir (string): Path to the h5 file with annotations.
            img_dir (string): Path to the h5 file with image features
            mode (string): Mode of train or test
        """
        self.qa_dir = opt.qa_dir
        self.vocab_dir = opt.vocab_dir
        self.imgFolder = self.qa_dir+'/sclevr/images/'

        # qa h5
        if mode == 'train':
            file = h5py.File(os.path.join(self.vocab_dir, 'annotation_sclevr_train.h5'), 'r')
            self.qas = {}
            self.qas['question'] = torch.from_numpy(np.int64(file['/ques_train'][:]))
            self.qas['question_id'] = torch.from_numpy(np.int64(file['/question_id_train'][:]))
            self.qas['img_id'] = torch.from_numpy(np.int32(file['/img_id_train'][:]))
            self.qas['answers'] = file['/answers'][:]
            file.close()
            self.trees = read_json(os.path.join(self.qa_dir, 'parsed_tree/sclevr_train_sorted_remain_trees.json'))
            self.types = read_json(os.path.join(self.qa_dir, 'sclevr/sclevr_train_type.json'))
        else:
            file = h5py.File(os.path.join(self.vocab_dir, 'annotation_sclevr_test.h5'), 'r')
            self.qas = {}
            self.qas['question'] = torch.from_numpy(np.int64(file['/ques_test'][:]))
            self.qas['question_id'] = torch.from_numpy(np.int64(file['/question_id_test'][:]))
            self.qas['img_id'] = torch.from_numpy(np.int32(file['/img_id_test'][:]))
            self.qas['answers'] = file['/answers'][:]
            file.close()
            self.trees = read_json(os.path.join(self.qa_dir, 'parsed_tree/sclevr_test_sorted_remain_trees.json'))
            self.types = read_json(os.path.join(self.qa_dir, 'sclevr/sclevr_test_type.json'))
        # train_test json
        vocab = read_json(os.path.join(self.vocab_dir, 'Vocab.json'))
        ansVocab = read_json(os.path.join(self.vocab_dir, 'AnsVocab.json'))
        opt.vocab_size = len(vocab)
        opt.out_vocab_size = len(ansVocab)

        opt.sent_len = self.qas['question'].size(1)
        self.mode = mode
        self.preprocess = transforms.Compose([
           transforms.Scale((128,128)),
           transforms.ToTensor()
        ])

        print('    * sclevr-%s loaded' % mode)

    def __len__(self):
        return self.qas['question'].size(0)
    
    def __getitem__(self, idx):
        img_id = self.qas['img_id'][idx]
        answer = self.qas['answers'][idx][0] - 1
        answer = answer.item()
        qid = self.qas['question_id'][idx]
        
        def id2imgName(img_id, qid):
            if self.mode == 'train': return self.imgFolder+'/train/%d.png' % img_id
            else: return self.imgFolder+'/test/%d.png' % img_id

        def load_image(img_name):
            img_tensor = self.preprocess(Image.open(img_name).convert('RGB'))
            # print(img_tensor.size())
            # img_tensor.unsqueeze_(0)
            # print(img_tensor.size())
            return img_tensor
        
        img_name = id2imgName(img_id, qid)

        return self.qas['question'][idx], \
               qid, \
               answer, \
               load_image(img_name), \
               img_name, \
               self.types[qid], \
               self.trees[idx]
