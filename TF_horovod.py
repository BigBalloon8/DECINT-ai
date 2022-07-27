import tensorflow as tf
import horovod.tensorflow as hvd
import model

def run():
    # Initialize Horovod
    hvd.init()

    # Pin GPU to be used to process local rank (one GPU per process)
    gpus = tf.config.experimental.list_physical_devices('GPU')
    for gpu in gpus:
        tf.config.experimental.set_memory_growth(gpu, True)
    if gpus:
        tf.config.experimental.set_visible_devices(gpus[hvd.local_rank()], 'GPU')

    data = model.dataset()
    complete_model = model.model()
    loss = model.loss()
    opt = model.opt(size=hvd.size())

    checkpoint_dir = './checkpoints'
    checkpoint = tf.train.Checkpoint(model=complete_model, optimizer=complete_model)


    @tf.function
    def training_step(images, labels, first_batch):
        with tf.GradientTape() as tape:
            probs = complete_model(images, training=True)
            loss_value = loss(labels, probs)

        # Horovod: add Horovod Distributed GradientTape.
        tape = hvd.DistributedGradientTape(tape)

        grads = tape.gradient(loss_value, complete_model.trainable_variables)
        opt.apply_gradients(zip(grads, complete_model.trainable_variables))

        if first_batch:
            hvd.broadcast_variables(complete_model.variables, root_rank=0)
            hvd.broadcast_variables(opt.variables(), root_rank=0)

        return loss_value


    # Horovod: adjust number of steps based on number of GPUs.
    for batch, (images, labels) in enumerate(data.take(10000 // hvd.size())):
        loss_value = training_step(images, labels, batch == 0)

        if batch % 10 == 0 and hvd.local_rank() == 0:
            print('Step #%d\tLoss: %.6f' % (batch, loss_value))

    if hvd.rank() == 0:
        checkpoint.save(checkpoint_dir)

    complete_model.save("./model.h5")

if __name__ == '__main__':
    run()