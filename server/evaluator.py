import tensorflow as tf
import pickle
from keras.models import load_model
from keras import layers
from keras.saving import register_keras_serializable
import os, pathlib

# =================================================
# TransformerEncoder
# =================================================
@register_keras_serializable()
class TransformerEncoder(layers.Layer):
    def __init__(self, d_model, num_heads, dff, rate=0.1, **kwargs):
        super().__init__(**kwargs)
        self.mha = layers.MultiHeadAttention(num_heads=num_heads, key_dim=d_model)
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
# Load model & tokenizer
# =================================================
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
MODEL_PATH = os.path.join(BASE_DIR, "static/model/model_4score.keras")
TOKENIZER_PATH = os.path.join(BASE_DIR, "static/model/tokenizer.pkl")
MAX_LEN = 197

model = load_model(
    MODEL_PATH,
    custom_objects={"TransformerEncoder": TransformerEncoder},
    compile=False
)

with open(TOKENIZER_PATH, "rb") as f:
    tokenizer = pickle.load(f)

# =================================================
# Public API
# =================================================
def score_sentences(sentences: list[str]) -> dict:
    """
    sentences: [persona 3 + user 3]
    """

    if len(sentences) != 6:
        raise ValueError("Exactly 6 sentences required")

    merged = " ".join(sentences)

    seq = tokenizer.texts_to_sequences([merged])
    pad = tf.keras.preprocessing.sequence.pad_sequences(seq, maxlen=MAX_LEN)

    pred = model.predict(pad, verbose=0)[0]

    return {
        "friend_user": float(pred[0]),
        "attract_user": float(pred[1]),
        "fun_user": float(pred[2]),
        "blri_user": float(pred[3]),
    }
