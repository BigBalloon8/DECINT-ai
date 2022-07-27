import torch
import model


def run():
    dataset = model.dataset()
    complete_model = model.model()
    complete_model = complete_model.cuda()
    loss = model.loss()
    opt = model.opt()