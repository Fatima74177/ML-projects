"""Transformer encoder implementation."""
import torch
import torch.nn as nn
from .attention import MultiHeadAttention


class FeedForwardNetwork(nn.Module):
    """Feed-Forward Network (FFN) component of transformer.
    
    FFN(x) = max(0, x * W1 + b1) * W2 + b2
    """
    
    def __init__(self, d_model, d_ff, dropout=0.1, activation='relu'):
        super(FeedForwardNetwork, self).__init__()
        self.linear1 = nn.Linear(d_model, d_ff)
        self.linear2 = nn.Linear(d_ff, d_model)
        self.dropout = nn.Dropout(dropout)
        
        if activation == 'relu':
            self.activation = nn.ReLU()
        elif activation == 'gelu':
            self.activation = nn.GELU()
        else:
            self.activation = nn.ReLU()
    
    def forward(self, x):
        """
        Args:
            x: Input tensor (batch_size, seq_len, d_model)
        
        Returns:
            FFN output
        """
        x = self.linear1(x)
        x = self.activation(x)
        x = self.dropout(x)
        x = self.linear2(x)
        return x


class TransformerEncoderLayer(nn.Module):
    """Single Transformer Encoder Layer.
    
    Architecture:
        Input
          ↓
        Multi-Head Attention
          ↓
        Add & LayerNorm
          ↓
        Feed-Forward Network
          ↓
        Add & LayerNorm
          ↓
        Output
    """
    
    def __init__(self, d_model, num_heads, d_ff, dropout=0.1):
        super(TransformerEncoderLayer, self).__init__()
        
        # Multi-head attention
        self.mha = MultiHeadAttention(d_model, num_heads, dropout)
        self.norm1 = nn.LayerNorm(d_model)
        self.dropout1 = nn.Dropout(dropout)
        
        # Feed-forward network
        self.ffn = FeedForwardNetwork(d_model, d_ff, dropout)
        self.norm2 = nn.LayerNorm(d_model)
        self.dropout2 = nn.Dropout(dropout)
    
    def forward(self, x, mask=None):
        """
        Args:
            x: Input tensor (batch_size, seq_len, d_model)
            mask: Optional attention mask
        
        Returns:
            Encoded output
        """
        # Multi-head attention with residual connection
        attn_output, _ = self.mha(x, x, x, mask)
        attn_output = self.dropout1(attn_output)
        x = self.norm1(x + attn_output)
        
        # Feed-forward with residual connection
        ffn_output = self.ffn(x)
        ffn_output = self.dropout2(ffn_output)
        x = self.norm2(x + ffn_output)
        
        return x


class TransformerEncoder(nn.Module):
    """Transformer Encoder consisting of multiple encoder layers."""
    
    def __init__(self, d_model, num_heads, d_ff, num_layers, dropout=0.1):
        super(TransformerEncoder, self).__init__()
        
        self.layers = nn.ModuleList([
            TransformerEncoderLayer(d_model, num_heads, d_ff, dropout)
            for _ in range(num_layers)
        ])
        
        self.norm = nn.LayerNorm(d_model)
    
    def forward(self, x, mask=None):
        """
        Args:
            x: Input tensor (batch_size, seq_len, d_model)
            mask: Optional attention mask
        
        Returns:
            Encoded representation
        """
        for layer in self.layers:
            x = layer(x, mask)
        
        x = self.norm(x)
        return x


if __name__ == "__main__":
    # Test FeedForwardNetwork
    print("Testing Feed-Forward Network:")
    d_model = 512
    d_ff = 2048
    ffn = FeedForwardNetwork(d_model, d_ff)
    
    batch_size, seq_len = 2, 10
    x = torch.randn(batch_size, seq_len, d_model)
    output = ffn(x)
    
    print(f"Input shape: {x.shape}")
    print(f"Output shape: {output.shape}")
    print()
    
    # Test TransformerEncoderLayer
    print("Testing Transformer Encoder Layer:")
    num_heads = 8
    encoder_layer = TransformerEncoderLayer(d_model, num_heads, d_ff)
    
    x = torch.randn(batch_size, seq_len, d_model)
    output = encoder_layer(x)
    
    print(f"Input shape: {x.shape}")
    print(f"Output shape: {output.shape}")
    print()
    
    # Test TransformerEncoder
    print("Testing Transformer Encoder:")
    num_layers = 6
    encoder = TransformerEncoder(d_model, num_heads, d_ff, num_layers)
    
    x = torch.randn(batch_size, seq_len, d_model)
    output = encoder(x)
    
    print(f"Input shape: {x.shape}")
    print(f"Output shape: {output.shape}")
