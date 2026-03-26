import tensorflow as tf
from tensorflow.keras.layers import Layer

class L2Normalization(Layer):

    def call(self, inputs):
        return tf.math.l2_normalize(inputs, axis=1)

    def get_config(self):
        return super().get_config()
