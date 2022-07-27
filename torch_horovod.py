import torch
import model
import horovod.torch as hvd

def run():
    
    hvd.init()

    torch.cuda.set_device(hvd.local_rank())

    dataset = model.dataset()
    complete_model = model.model()
    complete_model = complete_model.cuda()
    loss = model.loss()
    opt = model.opt()

    train_sampler = torch.utils.data.distributed.DistributedSampler(
        dataset, num_replicas=hvd.size(), rank=hvd.rank())

    train_loader = torch.utils.data.DataLoader(dataset, batch_size=..., sampler=train_sampler)

    opt = hvd.DistributedOptimizer(opt, named_parameters=complete_model.named_parameters())

    hvd.broadcast_parameters(complete_model.state_dict(), root_rank=0)

    for epoch in range(100):
        for batch_idx, (data, target) in enumerate(train_loader):
            opt.zero_grad()
            output = complete_model(data)
            loss = loss(output, target)
            loss.backward()
            opt.step()

    torch.save(complete_model, "./model.pt")