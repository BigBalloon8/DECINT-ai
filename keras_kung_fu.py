import tensorflow as tf
from kungfu.tensorflow.optimizers import PairAveragingOptimizer
from kungfu.tensorflow.initializer import BroadcastGlobalVariablesCallback
import model
import keras


def run():

    data = model.dataset()
    complete_model = model.model()
    loss = model.loss()
    opt = model.opt()

    opt = PairAveragingOptimizer(opt)

    complete_model.compile(loss=loss,
                           optimizer=opt,
                           metrics=["accuracy"]
                           )

    callbacks = [
        BroadcastGlobalVariablesCallback()
    ]

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
                       steps_per_epoch=model.STEP_PER_EPOCH,max_queue_size=model.MAX_QUEUE_SIZE,
                       callbacks=callbacks
                      )
    complete_model.save("./model.h5")

run()