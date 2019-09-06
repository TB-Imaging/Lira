import keras
from keras.models import load_model
model = load_model("type_one_classifier.h5")

for layer in model.layers:
    print(layer.input_shape, "->", layer, "->", layer.output_shape)
    try:
        print("\t", layer.activation)
    except: pass
    try:
        print("\t", layer.kernel_size)
    except: pass
    try:
        print("\t", layer.filters)
    except: pass
    try:
        print("\t", layer.strides)
    except: pass

