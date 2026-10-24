import keras
from keras import ops
from keras.layers import (
    Layer, Input, Bidirectional, LSTM, Dense,
    Dropout, BatchNormalization, LayerNormalization, Concatenate
)
from keras.models import Model

@keras.utils.register_keras_serializable(package="CustomLayers")
class TemporalAttention(Layer):
    """
    Custom Temporal Attention Mechanism for Bi-LSTM.
    Projects timestep hidden states via a non-linear activation (tanh),
    calculates normalized attention scores across timesteps, and computes
    a weighted temporal context vector.
    
    Compatible with Keras 3 serialization and Phase 6 XAI extraction.
    """
    def __init__(self, **kwargs):
        super(TemporalAttention, self).__init__(**kwargs)

    def build(self, input_shape):
        hidden_dim = input_shape[-1]
        self.dense_proj = Dense(64, activation="tanh", name="attn_proj")
        self.W = self.add_weight(
            name="attn_W",
            shape=(64, 1),
            initializer="glorot_uniform",
            trainable=True
        )
        self.b = self.add_weight(
            name="attn_b",
            shape=(1,),
            initializer="zeros",
            trainable=True
        )
        super(TemporalAttention, self).build(input_shape)

    def call(self, inputs, return_attention_weights=False):
        """
        inputs shape: (batch_size, timesteps, hidden_dim)
        score shape : (batch_size, timesteps, 1)
        weights shape: (batch_size, timesteps, 1)
        context shape: (batch_size, hidden_dim)
        """
        proj = self.dense_proj(inputs)
        score = ops.matmul(proj, self.W) + self.b
        weights = ops.softmax(score, axis=1)
        context = ops.sum(inputs * weights, axis=1)
        
        weights_squeezed = ops.squeeze(weights, axis=-1)
        
        if return_attention_weights:
            return context, weights_squeezed
        return context, weights_squeezed

    def get_config(self):
        config = super(TemporalAttention, self).get_config()
        return config


def build_bilstm_attention_model(
    seq_shape: tuple = (40, 4),
    static_shape: tuple = (70,),
    num_classes: int = 3,
    lstm_units: int = 64,
    static_dense_units: tuple = (64, 32),
    fusion_dense_units: int = 64,
    dropout_rate: float = 0.2
) -> tuple:
    """
    Builds the two-input Bi-LSTM + Attention + Static Feature Fusion Neural Network architecture.
    
    Returns:
      model: Classification Model accepting [seq_input, static_input] -> softmax output (3 classes)
      attention_extractor: Extractor Model accepting seq_input -> attention weights (40 timesteps)
    """
    # --------------------------------------------------------------------------
    # INPUT 1: SEQUENTIAL INPUT (40 timesteps, 4 features)
    # --------------------------------------------------------------------------
    seq_input = Input(shape=seq_shape, name="seq_input")
    
    # Bi-LSTM Layer (returns sequence representation at each timestep)
    bilstm = Bidirectional(
        LSTM(lstm_units, return_sequences=True),
        name="bilstm_layer"
    )(seq_input)
    
    # Custom Attention Layer
    attn_layer = TemporalAttention(name="temporal_attention")
    context, attn_weights = attn_layer(bilstm, return_attention_weights=True)

    # --------------------------------------------------------------------------
    # INPUT 2: STATIC INPUT (70 features)
    # --------------------------------------------------------------------------
    static_input = Input(shape=static_shape, name="static_input")
    
    x_stat = Dense(static_dense_units[0], activation="relu", name="static_dense_1")(static_input)
    x_stat = LayerNormalization(name="static_ln_1")(x_stat)
    x_stat = Dropout(dropout_rate, name="static_drop_1")(x_stat)
    
    x_stat = Dense(static_dense_units[1], activation="relu", name="static_dense_2")(x_stat)
    x_stat = Dropout(0.1, name="static_drop_2")(x_stat)

    # --------------------------------------------------------------------------
    # FUSION & CLASSIFICATION BRANCH
    # --------------------------------------------------------------------------
    fused = Concatenate(name="fusion_concat")([context, x_stat])
    fused = Dense(fusion_dense_units, activation="relu", name="fusion_dense")(fused)
    fused = Dropout(dropout_rate, name="fusion_drop")(fused)
    
    output = Dense(num_classes, activation="softmax", name="engagement_output")(fused)

    # Classification Model
    model = Model(inputs=[seq_input, static_input], outputs=output, name="BiLSTM_Attention_Engagement_Model")
    
    # Standalone Attention Extractor Model for Phase 6 XAI
    attention_extractor = Model(inputs=seq_input, outputs=attn_weights, name="Attention_Extractor_Model")

    return model, attention_extractor


if __name__ == "__main__":
    model, attn_extractor = build_bilstm_attention_model()
    model.compile(optimizer="adam", loss="sparse_categorical_crossentropy", metrics=["accuracy"])
    model.summary()
    print("\n -> Bi-LSTM + Attention Model Architecture defined successfully.")
