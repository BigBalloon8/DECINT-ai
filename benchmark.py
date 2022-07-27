import tensorflow as tf
import tensorflow.keras as keras
import time



def test():
    #add BENCHMARK protocol
    class TimeHistory(keras.callbacks.Callback):
        def on_train_begin(self, logs={}):
            self.times = []

        def on_epoch_begin(self, batch, logs={}):
            self.epoch_time_start = time.time()

        def on_epoch_end(self, batch, logs={}):
            self.times.append(time.time() - self.epoch_time_start)

    strategy = tf.distribute.MirroredStrategy()
    print('Number of devices: {}'.format(strategy.num_replicas_in_sync))

    (x_train, y_train), (x_test, y_test) = keras.datasets.cifar100.load_data()
    print("size of data: ", x_train.nbytes/1e6, "MB")
    x_train = x_train.astype('float32')/255.0
    y_train = keras.utils.to_categorical(y_train, 100)


    def resnet50(input_shape):
        model = keras.applications.ResNet50(include_top=False, weights=None, input_tensor=input_shape, classes=10, pooling='avg', )
        return model

    with strategy.scope():
        model = keras.Sequential()
        model.add(resnet50(keras.Input(shape=(32, 32, 3))))
        # print(model.summary())
        model.add(keras.layers.Flatten())
        model.add(keras.layers.Dense(100, activation='softmax'))

        model.compile(optimizer=keras.optimizers.Adam(lr=0.0001),
                      loss="categorical_crossentropy",
                      metrics=["accuracy"]
                      )
    time_callback = TimeHistory()
    model.fit(x_train, y_train, batch_size=64, epochs=50, verbose=1, callbacks=[time_callback])
    return (sum(time_callback.times)/len(time_callback.times))

print(test())
