"""Attention mechanisms for transformers."""
import math
import torch
import torch.nn as nn
import torch.nn.functional as F


class ScaledDotProductAttention(nn.Module):
    """Scaled Dot-Product Attention mechanism.
    
    Formula: Attention(Q, K, V) = softmax(Q * K^T / sqrt(d_k)) * V
    """
    
    def __init__(self, dropout=0.1):
        super(ScaledDotProductAttention, self).__init__()
        self.dropout = nn.Dropout(dropout)
    
    def forward(self, query, key, value, mask=None):
        """
        Args:
            query: Query tensor (batch_size, seq_len, d_k)
            key: Key tensor (batch_size, seq_len, d_k)
            value: Value tensor (batch_size, seq_len, d_v)
            mask: Optional mask tensor
        
        Returns:
            output: Attention output
            attention_weights: Attention weights
        """
        d_k = query.size(-1)
        
        # Compute attention scores: Q * K^T / sqrt(d_k)
        scores = torch.matmul(query, key.transpose(-2, -1)) / math.sqrt(d_k)
        
        # Apply mask if provided
        if mask is not None:
            scores = scores.masked_fill(mask == 0, -1e9)
        
        # Apply softmax to get attention weights
        attention_weights = F.softmax(scores, dim=-1)
        
        # Apply dropout
        attention_weights = self.dropout(attention_weights)
        
        # Multiply by values
        output = torch.matmul(attention_weights, value)
        
        return output, attention_weights


class MultiHeadAttention(nn.Module):
    """Multi-Head Attention mechanism.
    
    Multiple attention heads allow the model to attend to different representation subspaces.
    """
    
    def __init__(self, d_model, num_heads, dropout=0.1):
        super(MultiHeadAttention, self).__init__()
        assert d_model % num_heads == 0, "d_model must be divisible by num_heads"
        
        self.d_model = d_model
        self.num_heads = num_heads
        self.d_k = d_model // num_heads
        
        # Linear transformations for Q, K, V, and output
        self.W_q = nn.Linear(d_model, d_model)
        self.W_k = nn.Linear(d_model, d_model)
        self.W_v = nn.Linear(d_model, d_model)
        self.W_o = nn.Linear(d_model, d_model)
        
        self.attention = ScaledDotProductAttention(dropout)
        self.dropout = nn.Dropout(dropout)
    
    def forward(self, query, key, value, mask=None):
        """
        Args:
            query: Query tensor (batch_size, seq_len, d_model)
            key: Key tensor (batch_size, seq_len, d_model)
            value: Value tensor (batch_size, seq_len, d_model)
            mask: Optional attention mask
        
        Returns:
            output: Multi-head attention output
            attention_weights: Attention weights from last head
        """
        batch_size = query.size(0)
        
        # Linear projection and split into heads
        query = self.W_q(query).view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)
        key = self.W_k(key).view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)
        value = self.W_v(value).view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)
        
        # Apply attention
        attention_output, attention_weights = self.attention(query, key, value, mask)
        
        # Concatenate heads
        attention_output = attention_output.transpose(1, 2).contiguous()
        attention_output = attention_output.view(batch_size, -1, self.d_model)
        
        # Final linear transformation
        output = self.W_o(attention_output)
        output = self.dropout(output)
        
        return output, attention_weights


if __name__ == "__main__":
    # Test ScaledDotProductAttention
    print("Testing Scaled Dot-Product Attention:")
    attn = ScaledDotProductAttention()
    batch_size, seq_len, d_k = 2, 4, 64
    query = torch.randn(batch_size, seq_len, d_k)
    key = torch.randn(batch_size, seq_len, d_k)
    value = torch.randn(batch_size, seq_len, d_k)
    
    output, weights = attn(query, key, value)
    print(f"Output shape: {output.shape}")
    print(f"Attention weights shape: {weights.shape}")
    print()
    
    # Test MultiHeadAttention
    print("Testing Multi-Head Attention:")
    d_model = 512
    num_heads = 8
    mha = MultiHeadAttention(d_model, num_heads)
    query = torch.randn(batch_size, seq_len, d_model)
    key = torch.randn(batch_size, seq_len, d_model)
    value = torch.randn(batch_size, seq_len, d_model)
    
    output, weights = mha(query, key, value)
    print(f"Output shape: {output.shape}")
    print(f"Attention weights shape: {weights.shape}")
