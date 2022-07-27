import tensorflow as tf
import horovod.keras as hvd
import model
import keras


def run():

    # Horovod: initialize Horovod.
    hvd.init()

    # Horovod: pin GPU to be used to process local rank (one GPU per process)
    gpus = tf.config.experimental.list_physical_devices('GPU')
    for gpu in gpus:
        tf.config.experimental.set_memory_growth(gpu, True)
    if gpus:
        tf.config.experimental.set_visible_devices(gpus[hvd.local_rank()], 'GPU')

    data = model.dataset()
    complete_model = model.model()
    loss = model.loss()
    opt = model.opt()

    opt = hvd.DistributedOptimizer(opt)

    complete_model.compile(loss=loss,
                           optimizer=opt,
                           metrics=["accuracy"]
                           )

    callbacks = [
        # Horovod: broadcast initial variable states from rank 0 to all other processes.
        # This is necessary to ensure consistent initialization of all workers when
        # training is started with random weights or restored from a checkpoint.
        hvd.callbacks.BroadcastGlobalVariablesCallback(0),
    ]

    if hvd.rank() == 0:
        callbacks.append(keras.callbacks.ModelCheckpoint('./checkpoint-{epoch}.h5'))

    if not model.EPOCHS:
        model.EPOCHS = 64
    if not model.BATCH_SIZE:
        model.BATCH_SIZE = None
    if not model.SHUFFLE:
        model.SHUFFLE = True
    if not model.CLASS_WEIGHT:
        model.CLASS_WEIGHT = None
    if not model.SAMPLE_WEIGHT:
        model.SAMPLE_WEIGHT = None
    if not model.INITIAL_EPOCH:
        model.INITIAL_EPOCH = 0
    if not model.STEP_PER_EPOCH:
        model.STEP_PER_EPOCH = None
    if not model.MAX_QUEUE_SIZE:
        model.MAX_QUEUE_SIZE = 10

    complete_model.fit(data, epochs=model.EPOCHS, verbose=0, batch_size=model.BATCH_SIZE,
                       shuffle=model.SHUFFLE, class_weight=model.CLASS_WEIGHT,
                       sample_weight=model.SAMPLE_WEIGHT, initial_epoch=model.INITIAL_EPOCH,
                       steps_per_epoch=model.STEP_PER_EPOCH, max_queue_size=model.MAX_QUEUE_SIZE,
                       callbacks=callbacks
                       )
    complete_model.save("./model.h5")

run()