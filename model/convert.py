"""
Convert a trained Keras/SavedModel to int8 TFLite and generate C headers.

Usage:
    python convert.py --model saved_model/ --dataset mnist --output-dir ../firmware
    python convert.py --model model.h5 --calib-dir calib_images/ --output-dir ../firmware
    python convert.py --model model.tflite --print-quant-params   # inspect only
    python convert.py --model model.tflite --export-c-array       # C header only
    python convert.py --model model.tflite --export-test-vectors 50
"""

import argparse
import os
import struct
import numpy as np

def load_calibration_data(dataset_name, calib_dir, n_samples=100):
    if dataset_name == "mnist":
        import tensorflow as tf
        (_, _), (x_test, _) = tf.keras.datasets.mnist.load_data()
        x = x_test[:n_samples].astype("float32") / 255.0
        return x.reshape(n_samples, -1, 1)
    elif calib_dir:
        from PIL import Image
        images = []
        for f in sorted(os.listdir(calib_dir))[:n_samples]:
            img = Image.open(os.path.join(calib_dir, f)).convert("L")
            images.append(np.array(img, dtype="float32") / 255.0)
        return np.array(images)[..., np.newaxis]
    else:
        raise ValueError("Provide --dataset or --calib-dir")


def convert(model_path, calib_data):
    import tensorflow as tf

    if model_path.endswith(".tflite"):
        with open(model_path, "rb") as f:
            return f.read()

    model = tf.keras.models.load_model(model_path)

    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
    converter.inference_input_type  = tf.int8
    converter.inference_output_type = tf.int8

    def rep_dataset():
        for sample in calib_data:
            yield [sample[np.newaxis].astype("float32")]

    converter.representative_dataset = rep_dataset
    return converter.convert()


def print_quant_params(tflite_bytes):
    import tensorflow as tf
    interp = tf.lite.Interpreter(model_content=tflite_bytes)
    interp.allocate_tensors()
    inp  = interp.get_input_details()[0]
    outp = interp.get_output_details()[0]
    print(f"INPUT  shape={inp['shape']}  scale={inp['quantization'][0]:.8f}  zero_point={inp['quantization'][1]}")
    print(f"OUTPUT shape={outp['shape']} scale={outp['quantization'][0]:.8f}  zero_point={outp['quantization'][1]}")
    print()
    print("Paste into firmware/<target>/include/model_config.h:")
    print(f"  #define MODEL_INPUT_SIZE        {int(np.prod(inp['shape'][1:]))}")
    print(f"  #define MODEL_NUM_CLASSES       {outp['shape'][1]}")
    print(f"  #define MODEL_INPUT_SCALE       {inp['quantization'][0]:.8f}f")
    print(f"  #define MODEL_INPUT_ZERO_POINT  {inp['quantization'][1]}")
    print(f"  #define MODEL_OUTPUT_SCALE      {outp['quantization'][0]:.8f}f")
    print(f"  #define MODEL_OUTPUT_ZERO_POINT {outp['quantization'][1]}")


def export_c_array(tflite_bytes, out_path):
    os.makedirs(out_path, exist_ok=True)
    header = os.path.join(out_path, "model_data.h")
    with open(header, "w") as f:
        f.write("#pragma once\n#include <stdint.h>\n\n")
        f.write(f"static const uint8_t g_model_data[] = {{\n  ")
        for i, b in enumerate(tflite_bytes):
            f.write(f"0x{b:02x},")
            if (i + 1) % 16 == 0:
                f.write("\n  ")
        f.write("\n};\n")
        f.write(f"static const int g_model_data_len = {len(tflite_bytes)};\n")
    print(f"Written: {header}")


def export_test_vectors(tflite_bytes, dataset_name, calib_dir, n, out_path):
    import tensorflow as tf
    data = load_calibration_data(dataset_name, calib_dir, n_samples=n)
    interp = tf.lite.Interpreter(model_content=tflite_bytes)
    interp.allocate_tensors()
    inp_detail = interp.get_input_details()[0]
    scale, zp   = inp_detail["quantization"]
    input_size  = int(np.prod(inp_detail["shape"][1:]))

    if dataset_name == "mnist":
        (_, _), (_, labels) = tf.keras.datasets.mnist.load_data()
        labels = labels[:n].tolist()
    else:
        labels = [-1] * n

    os.makedirs(out_path, exist_ok=True)
    header = os.path.join(out_path, "test_vectors.h")
    with open(header, "w") as f:
        f.write("#pragma once\n#include <stdint.h>\n\n")
        f.write(f"static const int TEST_COUNT = {n};\n\n")
        f.write(f"static const int test_labels[{n}] = {{\n  ")
        f.write(", ".join(str(l) for l in labels))
        f.write("\n};\n\n")
        f.write(f"static const int8_t test_inputs[{n}][{input_size}] = {{\n")
        for sample in data[:n]:
            q = np.clip(
                np.round(sample.flatten() / scale + zp), -128, 127
            ).astype(np.int8)
            f.write("  {" + ", ".join(str(int(v)) for v in q) + "},\n")
        f.write("};\n")
    print(f"Written: {header}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model",              required=True)
    ap.add_argument("--dataset",            default="mnist")
    ap.add_argument("--calib-dir",          default=None)
    ap.add_argument("--output-dir",         default=".")
    ap.add_argument("--print-quant-params", action="store_true")
    ap.add_argument("--export-c-array",     action="store_true")
    ap.add_argument("--export-test-vectors",type=int, default=0)
    args = ap.parse_args()

    if args.model.endswith(".tflite"):
        with open(args.model, "rb") as f:
            tflite_bytes = f.read()
    else:
        calib = load_calibration_data(args.dataset, args.calib_dir)
        tflite_bytes = convert(args.model, calib)
        tflite_out = os.path.join(args.output_dir, "model.tflite")
        os.makedirs(args.output_dir, exist_ok=True)
        with open(tflite_out, "wb") as f:
            f.write(tflite_bytes)
        print(f"Saved: {tflite_out}")

    if args.print_quant_params or not (args.export_c_array or args.export_test_vectors):
        print_quant_params(tflite_bytes)

    if args.export_c_array:
        for target in ["stm32n6", "esp32", "arduino/nano33_classifier"]:
            export_c_array(tflite_bytes,
                           os.path.join(args.output_dir, "firmware", target))

    if args.export_test_vectors:
        for target in ["stm32n6/src", "esp32/main", "arduino/nano33_classifier"]:
            export_test_vectors(tflite_bytes, args.dataset, args.calib_dir,
                                args.export_test_vectors,
                                os.path.join(args.output_dir, "firmware", target))


if __name__ == "__main__":
    main()
