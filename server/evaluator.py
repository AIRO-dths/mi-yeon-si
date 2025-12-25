import os
import pathlib
import pickle
import tensorflow as tf
from keras import layers
from keras.models import load_model
from keras.saving import register_keras_serializable

# =================================================
# TransformerEncoder (Custom Layer)
# =================================================
@register_keras_serializable()
class TransformerEncoder(layers.Layer):
    def __init__(self, d_model, num_heads, dff, rate=0.1, **kwargs):
        super().__init__(**kwargs)
        self.mha = layers.MultiHeadAttention(
            num_heads=num_heads,
            key_dim=d_model
        )
        self.ffn = tf.keras.Sequential([
            layers.Dense(dff, activation="relu"),
            layers.Dense(d_model),
        ])
        self.norm1 = layers.LayerNormalization()
        self.norm2 = layers.LayerNormalization()
        self.drop1 = layers.Dropout(rate)
        self.drop2 = layers.Dropout(rate)

    def call(self, x, training=False):
        attn = self.mha(x, x, x)
        attn = self.drop1(attn, training=training)
        out1 = self.norm1(x + attn)

        ffn_out = self.ffn(out1)
        ffn_out = self.drop2(ffn_out, training=training)
        return self.norm2(out1 + ffn_out)


# =================================================
# Path config
# =================================================
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "static" / "model" / "model_4score.keras"
TOKENIZER_PATH = BASE_DIR / "static" / "model" / "tokenizer.pkl"
MAX_LEN = 197

FRIEND_AVR = 3.3679
ATTRACT_AVR = 3.2738
FUN_AVR = 3.2076
BLRI_AVR = 51.5315


# =================================================
# Lazy-loaded globals
# =================================================
_model = None
_tokenizer = None


# =================================================
# Loader (called once)
# =================================================
def load_evaluator():
    """
    TensorFlow / Keras model & tokenizer loader.
    Safe to call multiple times (loads once).
    """
    global _model, _tokenizer

    if _model is not None and _tokenizer is not None:
        return

    print("🔹 Loading Keras model...", flush=True)

    _model = load_model(
        MODEL_PATH,
        custom_objects={"TransformerEncoder": TransformerEncoder},
        compile=False
    )

    print("🔹 Loading tokenizer...", flush=True)

    with open(TOKENIZER_PATH, "rb") as f:
        _tokenizer = pickle.load(f)

    print("✅ Evaluator ready", flush=True)


# =================================================
# Public API
# =================================================
def score_sentences(sentences: list[str]) -> dict:
    """
    sentences: list of exactly 6 strings
    """
    if len(sentences) != 6:
        raise ValueError("Exactly 6 sentences required")

    # ensure model is loaded
    load_evaluator()

    merged = " ".join(sentences)

    seq = _tokenizer.texts_to_sequences([merged])
    pad = tf.keras.preprocessing.sequence.pad_sequences(
        seq,
        maxlen=MAX_LEN
    )

    pred = _model.predict(pad, verbose=0)[0]

    return {
        "friend_user": float(pred[0]/FRIEND_AVR),
        "attract_user": float(pred[1]/ATTRACT_AVR),
        "fun_user": float(pred[2]/FUN_AVR),
        "blri_user": float(pred[3]/BLRI_AVR),
    }
