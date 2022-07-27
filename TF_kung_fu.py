import tensorflow as tf
from kungfu.tensorflow import optimizers
from kungfu.tensorflow.initializer import broadcat_variables
import model

def run():

    data = model.dataset()
    complete_model = model.model()
    loss = model.loss()
    opt = model.opt()


    if model.OPT == "S-SGD":
        opt = optimizers.SynchronousSGDOptimizer(opt)
    elif model.OPT == "SMA":
        opt = optimizers.SynchronousAveragingOptimizer(opt)
    else:
        opt = optimizers.PairAveragingOptimizer(opt)

    @tf.function
    def training_step(images, labels, first_batch):
        with tf.GradientTape() as tape:
            probs = complete_model(images, training=True)
            loss_value = loss(labels, probs)

            grads = tape.gradient(loss_value,complete_model.trainable_variables)
            opt.apply_gradients(zip(grads, complete_model.trainable_variable))

            if first_batch:
                broadcat_variables(complete_model.variables)
                broadcat_variables(opt.variables())

            return loss_value
    for batch, (image, labels) in enumerate(data.take(10000)):
        loss_value = training_step(images, labels, batch == 0)

    complete_model.save("./model.h5")

run()