"""
Train a classification model and save it.
Default: MNIST (28x28 grayscale, 10 classes) — replace dataset/model for your use case.

Usage:
    python train.py
    python train.py --dataset cifar10 --epochs 20 --output saved_model/
"""

import argparse
import os
import numpy as np
import tensorflow as tf

def build_model(input_shape, num_classes):
    return tf.keras.Sequential([
        tf.keras.layers.Input(shape=input_shape),
        tf.keras.layers.Flatten(),
        tf.keras.layers.Dense(128, activation="relu"),
        tf.keras.layers.Dense(64,  activation="relu"),
        tf.keras.layers.Dense(num_classes, activation="softmax"),
    ])

def load_dataset(name):
    if name == "mnist":
        (x_train, y_train), (x_test, y_test) = tf.keras.datasets.mnist.load_data()
        x_train = x_train.astype("float32") / 255.0
        x_test  = x_test.astype("float32")  / 255.0
        return (x_train, y_train), (x_test, y_test), (28, 28, 1), 10
    elif name == "cifar10":
        (x_train, y_train), (x_test, y_test) = tf.keras.datasets.cifar10.load_data()
        x_train = x_train.astype("float32") / 255.0
        x_test  = x_test.astype("float32")  / 255.0
        y_train = y_train.flatten()
        y_test  = y_test.flatten()
        return (x_train, y_train), (x_test, y_test), (32, 32, 3), 10
    else:
        raise ValueError(f"Unknown dataset: {name}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="mnist")
    ap.add_argument("--epochs",  type=int, default=10)
    ap.add_argument("--output",  default="saved_model/")
    args = ap.parse_args()

    (x_train, y_train), (x_test, y_test), input_shape, num_classes = \
        load_dataset(args.dataset)

    model = build_model(input_shape, num_classes)
    model.summary()

    model.compile(
        optimizer="adam",
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    model.fit(x_train, y_train,
              epochs=args.epochs,
              validation_split=0.1,
              batch_size=64)

    loss, acc = model.evaluate(x_test, y_test, verbose=0)
    print(f"\nTest accuracy: {acc*100:.2f}%  (float32 baseline)")

    os.makedirs(args.output, exist_ok=True)
    model.save(args.output)
    print(f"Saved: {args.output}")
    print(f"\nNext step:")
    print(f"  python convert.py --model {args.output} --dataset {args.dataset} \\")
    print(f"    --export-c-array --export-test-vectors 100 --output-dir ..")

if __name__ == "__main__":
    main()
