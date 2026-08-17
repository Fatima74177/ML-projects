"""Transformer decoder implementation."""
import torch
import torch.nn as nn
from .attention import MultiHeadAttention
from .encoder import FeedForwardNetwork


class TransformerDecoderLayer(nn.Module):
    """Single Transformer Decoder Layer.
    
    Architecture:
        Input
          ↓
        Masked Multi-Head Self-Attention
          ↓
        Add & LayerNorm
          ↓
        Multi-Head Cross-Attention (with encoder output)
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
        super(TransformerDecoderLayer, self).__init__()
        
        # Self-attention
        self.self_mha = MultiHeadAttention(d_model, num_heads, dropout)
        self.norm1 = nn.LayerNorm(d_model)
        self.dropout1 = nn.Dropout(dropout)
        
        # Cross-attention
        self.cross_mha = MultiHeadAttention(d_model, num_heads, dropout)
        self.norm2 = nn.LayerNorm(d_model)
        self.dropout2 = nn.Dropout(dropout)
        
        # Feed-forward network
        self.ffn = FeedForwardNetwork(d_model, d_ff, dropout)
        self.norm3 = nn.LayerNorm(d_model)
        self.dropout3 = nn.Dropout(dropout)
    
    def forward(self, x, encoder_output, self_mask=None, cross_mask=None):
        """
        Args:
            x: Decoder input (batch_size, tgt_seq_len, d_model)
            encoder_output: Encoder output (batch_size, src_seq_len, d_model)
            self_mask: Self-attention mask (causal mask for autoregressive generation)
            cross_mask: Cross-attention mask
        
        Returns:
            Decoded output
        """
        # Self-attention with residual connection
        self_attn_output, _ = self.self_mha(x, x, x, self_mask)
        self_attn_output = self.dropout1(self_attn_output)
        x = self.norm1(x + self_attn_output)
        
        # Cross-attention with encoder output
        cross_attn_output, _ = self.cross_mha(x, encoder_output, encoder_output, cross_mask)
        cross_attn_output = self.dropout2(cross_attn_output)
        x = self.norm2(x + cross_attn_output)
        
        # Feed-forward with residual connection
        ffn_output = self.ffn(x)
        ffn_output = self.dropout3(ffn_output)
        x = self.norm3(x + ffn_output)
        
        return x


class TransformerDecoder(nn.Module):
    """Transformer Decoder consisting of multiple decoder layers."""
    
    def __init__(self, d_model, num_heads, d_ff, num_layers, dropout=0.1):
        super(TransformerDecoder, self).__init__()
        
        self.layers = nn.ModuleList([
            TransformerDecoderLayer(d_model, num_heads, d_ff, dropout)
            for _ in range(num_layers)
        ])
        
        self.norm = nn.LayerNorm(d_model)
    
    def forward(self, x, encoder_output, self_mask=None, cross_mask=None):
        """
        Args:
            x: Decoder input (batch_size, tgt_seq_len, d_model)
            encoder_output: Encoder output (batch_size, src_seq_len, d_model)
            self_mask: Self-attention mask (causal mask)
            cross_mask: Cross-attention mask
        
        Returns:
            Decoded representation
        """
        for layer in self.layers:
            x = layer(x, encoder_output, self_mask, cross_mask)
        
        x = self.norm(x)
        return x


def create_causal_mask(seq_len, device):
    """Create a causal mask for autoregressive generation.
    
    Prevents attention to future positions.
    """
    mask = torch.triu(torch.ones(seq_len, seq_len, device=device), diagonal=1).bool()
    return mask


if __name__ == "__main__":
    # Test TransformerDecoderLayer
    print("Testing Transformer Decoder Layer:")
    d_model = 512
    num_heads = 8
    d_ff = 2048
    
    decoder_layer = TransformerDecoderLayer(d_model, num_heads, d_ff)
    
    batch_size = 2
    src_seq_len = 10
    tgt_seq_len = 8
    
    encoder_output = torch.randn(batch_size, src_seq_len, d_model)
    decoder_input = torch.randn(batch_size, tgt_seq_len, d_model)
    
    # Create causal mask
    causal_mask = create_causal_mask(tgt_seq_len, decoder_input.device)
    
    output = decoder_layer(decoder_input, encoder_output, self_mask=causal_mask)
    
    print(f"Encoder output shape: {encoder_output.shape}")
    print(f"Decoder input shape: {decoder_input.shape}")
    print(f"Decoder output shape: {output.shape}")
    print(f"Causal mask shape: {causal_mask.shape}")
    print()
    
    # Test TransformerDecoder
    print("Testing Transformer Decoder:")
    num_layers = 6
    decoder = TransformerDecoder(d_model, num_heads, d_ff, num_layers)
    
    output = decoder(decoder_input, encoder_output, self_mask=causal_mask)
    
    print(f"Decoder output shape: {output.shape}")
