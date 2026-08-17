"""Positional encoding for transformers."""
import math
import torch
import torch.nn as nn


class PositionalEncoding(nn.Module):
    """Positional Encoding using sine and cosine functions.
    
    Formula:
        PE(pos, 2i) = sin(pos / 10000^(2i / d_model))
        PE(pos, 2i+1) = cos(pos / 10000^(2i / d_model))
    """
    
    def __init__(self, d_model, max_seq_len=5000, dropout=0.1):
        super(PositionalEncoding, self).__init__()
        self.dropout = nn.Dropout(p=dropout)
        
        # Create positional encoding matrix
        pe = torch.zeros(max_seq_len, d_model)
        position = torch.arange(0, max_seq_len, dtype=torch.float).unsqueeze(1)
        
        # Calculate the division term
        div_term = torch.exp(
            torch.arange(0, d_model, 2, dtype=torch.float) * 
            -(math.log(10000.0) / d_model)
        )
        
        # Apply sine to even indices
        pe[:, 0::2] = torch.sin(position * div_term)
        
        # Apply cosine to odd indices
        if d_model % 2 == 1:
            pe[:, 1::2] = torch.cos(position * div_term[:-1])
        else:
            pe[:, 1::2] = torch.cos(position * div_term)
        
        # Register as buffer (not a learnable parameter)
        self.register_buffer('pe', pe.unsqueeze(0))
    
    def forward(self, x):
        """
        Args:
            x: Input tensor (batch_size, seq_len, d_model)
        
        Returns:
            x + positional_encoding
        """
        # Add positional encoding to input
        x = x + self.pe[:, :x.size(1), :]
        return self.dropout(x)


class LearnedPositionalEncoding(nn.Module):
    """Learnable positional encoding."""
    
    def __init__(self, d_model, max_seq_len=5000, dropout=0.1):
        super(LearnedPositionalEncoding, self).__init__()
        self.pe = nn.Embedding(max_seq_len, d_model)
        self.dropout = nn.Dropout(p=dropout)
        self.max_seq_len = max_seq_len
    
    def forward(self, x):
        """
        Args:
            x: Input tensor (batch_size, seq_len, d_model)
        
        Returns:
            x + learned positional encoding
        """
        seq_len = x.size(1)
        positions = torch.arange(0, seq_len, dtype=torch.long, device=x.device).unsqueeze(0)
        pe = self.pe(positions)
        x = x + pe
        return self.dropout(x)


if __name__ == "__main__":
    # Test PositionalEncoding
    print("Testing Positional Encoding:")
    d_model = 512
    seq_len = 10
    batch_size = 2
    
    pe = PositionalEncoding(d_model)
    x = torch.randn(batch_size, seq_len, d_model)
    output = pe(x)
    
    print(f"Input shape: {x.shape}")
    print(f"Output shape: {output.shape}")
    print(f"Positional encoding matrix shape: {pe.pe.shape}")
    print()
    
    # Visualize positional encoding
    print("Sample positional encoding (first 10 positions, first 8 dimensions):")
    pe_only = pe.pe[0, :10, :8]
    print(pe_only)
    print()
    
    # Test LearnedPositionalEncoding
    print("Testing Learned Positional Encoding:")
    lpe = LearnedPositionalEncoding(d_model)
    x = torch.randn(batch_size, seq_len, d_model)
    output = lpe(x)
    
    print(f"Input shape: {x.shape}")
    print(f"Output shape: {output.shape}")
