"""
EngageAI Backend — services/ml_service.py

Singleton ML inference service. Loads the Bi-LSTM + Attention model and
FeaturePreprocessor ONCE at application startup via the FastAPI lifespan.
"""

import os
import sys
import json
import numpy as np
import pandas as pd

# ─── Python path setup ────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PREPROCESSING_DIR = os.path.join(BASE_DIR, "preprocessing")
MODELS_DIR = os.path.join(BASE_DIR, "models")

for p in [BASE_DIR, PREPROCESSING_DIR, MODELS_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

# ─── Import encoder_scaler explicitly BEFORE loading pickle ───────────────────
import encoder_scaler
FeaturePreprocessor = encoder_scaler.FeaturePreprocessor
sys.modules['encoder_scaler'] = encoder_scaler
sys.modules['__main__'].FeaturePreprocessor = FeaturePreprocessor

from bilstm_attention import TemporalAttention
import keras
import joblib

from ml.feature_mapping.app_to_model import (
    aggregate_weekly_sequence,
    build_static_features,
    has_sufficient_activity,
)

MODEL_PATH       = os.path.join(BASE_DIR, "saved_model", "bilstm_attention_model.keras")
PREPROCESSOR_PKL = os.path.join(BASE_DIR, "saved_model", "feature_preprocessor.pkl")

CLASS_LABELS = {0: "Low", 1: "Medium", 2: "High"}


class MLService:
    """
    Singleton that holds the loaded Keras model and FeaturePreprocessor.
    Instantiate once at startup; call predict() for each inference request.
    """

    def __init__(self):
        self._model       = None
        self._preprocessor = None
        self._attn_extractor = None

    def load(self):
        """Load model and preprocessor from disk. Call once at startup."""
        print("[MLService] Loading FeaturePreprocessor...")
        # Guarantee class is in sys.modules['__main__'] when unpickling
        import __main__
        setattr(__main__, 'FeaturePreprocessor', FeaturePreprocessor)

        self._preprocessor = joblib.load(PREPROCESSOR_PKL)
        print("[MLService] Loading Bi-LSTM + Attention model...")
        self._model = keras.models.load_model(
            MODEL_PATH,
            custom_objects={"TemporalAttention": TemporalAttention},
        )

        # Build lightweight attention extractor sub-model
        bilstm_layer = self._model.get_layer("bilstm_layer")
        attn_layer   = self._model.get_layer("temporal_attention")
        seq_in   = keras.Input(shape=(40, 4), name="attn_infer_input")
        lstm_out = bilstm_layer(seq_in)
        _, weights = attn_layer(lstm_out, return_attention_weights=True)
        self._attn_extractor = keras.Model(inputs=seq_in, outputs=weights, name="AttnExtractor")

        print("[MLService] Model and preprocessor loaded successfully.")

    @property
    def model(self):
        if self._model is None:
            raise RuntimeError("MLService not loaded. Call load() at startup.")
        return self._model

    @property
    def preprocessor(self):
        if self._preprocessor is None:
            raise RuntimeError("MLService not loaded. Call load() at startup.")
        return self._preprocessor

    def predict(
        self,
        activity_events,
        quiz_attempts,
        content_progress,
        user_profile: dict,
    ) -> dict:
        """
        Runs the complete inference pipeline for one student.
        Returns a dict with probabilities, predicted_class, engagement_level.
        """
        if not has_sufficient_activity(activity_events):
            return {
                "sufficient_data"    : False,
                "message"            : "Not enough learning activity yet. Keep watching videos and taking quizzes!",
                "predicted_class"    : None,
                "engagement_level"   : None,
                "low_probability"    : None,
                "medium_probability" : None,
                "high_probability"   : None,
                "confidence"         : None,
            }

        # 1. Build temporal sequence (40, 4)
        X_seq = aggregate_weekly_sequence(activity_events)  # (40, 4)

        # 2. Build static raw features
        raw_features = build_static_features(
            activity_events, quiz_attempts, content_progress, user_profile
        )

        # 3. Preprocess static features → (70,)
        df_raw = pd.DataFrame([raw_features])
        X_static_df = self._preprocessor.transform(df_raw)
        X_static = X_static_df.values.astype(np.float32)  # (1, 70)

        # 4. Reshape sequence for batch: (1, 40, 4)
        X_seq_batch = X_seq[np.newaxis, :, :]  # (1, 40, 4)

        # 5. Run model inference
        probs = self._model.predict([X_seq_batch, X_static], verbose=0)[0]  # (3,)
        pred_class = int(np.argmax(probs))

        return {
            "sufficient_data"    : True,
            "predicted_class"    : pred_class,
            "engagement_level"   : CLASS_LABELS[pred_class],
            "low_probability"    : float(f"{probs[0]:.4f}"),
            "medium_probability" : float(f"{probs[1]:.4f}"),
            "high_probability"   : float(f"{probs[2]:.4f}"),
            "confidence"         : float(f"{probs[pred_class]:.4f}"),
        }

    def extract_attention(self, activity_events, user_profile: dict = None) -> dict:
        """
        Extracts attention weights (40 timesteps) for one student's sequence.
        Returns week labels and normalized attention weights.
        """
        X_seq = aggregate_weekly_sequence(activity_events)
        X_seq_batch = X_seq[np.newaxis, :, :]

        attn_weights = self._attn_extractor.predict(X_seq_batch, verbose=0)[0]  # (40,)

        week_labels = ["Pre-course"] + [f"Week {w}" for w in range(1, 40)]
        return {
            "timestep_labels"  : week_labels,
            "attention_weights": [float(f"{w:.5f}") for w in attn_weights],
            "top_weeks": sorted(
                [{"week": week_labels[i], "weight": float(f"{attn_weights[i]:.5f}")}
                 for i in range(40)],
                key=lambda x: x["weight"],
                reverse=True
            )[:10],
        }

    def get_feature_names(self) -> list:
        return self._preprocessor.feature_names_out_


# ─── Global singleton ─────────────────────────────────────────────────────────
ml_service = MLService()
