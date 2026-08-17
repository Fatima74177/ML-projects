"""Full Transformer model implementation."""
import torch
import torch.nn as nn
from .attention import MultiHeadAttention
from .positional_encoding import PositionalEncoding
from .encoder import TransformerEncoder
from .decoder import TransformerDecoder, create_causal_mask


class Transformer(nn.Module):
    """Complete Transformer model (Encoder-Decoder architecture).
    
    Architecture:
        Embedding + Positional Encoding
          ↓
        Transformer Encoder (6+ layers)
          ↓
        Transformer Decoder (6+ layers with cross-attention)
          ↓
        Linear + Softmax for output probabilities
    """
    
    def __init__(self, vocab_size, d_model=512, num_heads=8, d_ff=2048, 
                 num_encoder_layers=6, num_decoder_layers=6, max_seq_len=5000, 
                 dropout=0.1, padding_idx=0):
        super(Transformer, self).__init__()
        
        self.d_model = d_model
        self.vocab_size = vocab_size
        
        # Embeddings
        self.embedding = nn.Embedding(vocab_size, d_model, padding_idx=padding_idx)
        self.positional_encoding = PositionalEncoding(d_model, max_seq_len, dropout)
        
        # Encoder
        self.encoder = TransformerEncoder(
            d_model, num_heads, d_ff, num_encoder_layers, dropout
        )
        
        # Decoder
        self.decoder = TransformerDecoder(
            d_model, num_heads, d_ff, num_decoder_layers, dropout
        )
        
        # Output layer
        self.output_linear = nn.Linear(d_model, vocab_size)
        
        # Initialize weights
        self._init_weights()
    
    def _init_weights(self):
        """Initialize model weights."""
        for p in self.parameters():
            if p.dim() > 1:
                nn.init.xavier_uniform_(p)
    
    def encode(self, src, src_mask=None):
        """Encode source sequence.
        
        Args:
            src: Source token IDs (batch_size, src_seq_len)
            src_mask: Source attention mask
        
        Returns:
            Encoder output
        """
        # Embedding and positional encoding
        src_embed = self.embedding(src) * (self.d_model ** 0.5)
        src_embed = self.positional_encoding(src_embed)
        
        # Encode
        encoder_output = self.encoder(src_embed, src_mask)
        return encoder_output
    
    def decode(self, tgt, encoder_output, tgt_mask=None, cross_mask=None):
        """Decode target sequence.
        
        Args:
            tgt: Target token IDs (batch_size, tgt_seq_len)
            encoder_output: Output from encoder
            tgt_mask: Target attention mask (causal mask)
            cross_mask: Cross-attention mask
        
        Returns:
            Decoder output
        """
        # Embedding and positional encoding
        tgt_embed = self.embedding(tgt) * (self.d_model ** 0.5)
        tgt_embed = self.positional_encoding(tgt_embed)
        
        # Decode
        decoder_output = self.decoder(tgt_embed, encoder_output, tgt_mask, cross_mask)
        return decoder_output
    
    def forward(self, src, tgt, src_mask=None, tgt_mask=None, cross_mask=None):
        """
        Args:
            src: Source token IDs (batch_size, src_seq_len)
            tgt: Target token IDs (batch_size, tgt_seq_len)
            src_mask: Source attention mask
            tgt_mask: Target attention mask (causal)
            cross_mask: Cross-attention mask
        
        Returns:
            logits: Output logits (batch_size, tgt_seq_len, vocab_size)
        """
        # Encode
        encoder_output = self.encode(src, src_mask)
        
        # Decode
        decoder_output = self.decode(tgt, encoder_output, tgt_mask, cross_mask)
        
        # Output projection
        logits = self.output_linear(decoder_output)
        
        return logits


class TransformerEncoderOnly(nn.Module):
    """Transformer with only encoder (for classification tasks)."""
    
    def __init__(self, vocab_size, d_model=512, num_heads=8, d_ff=2048, 
                 num_layers=6, max_seq_len=5000, dropout=0.1, 
                 num_classes=2, padding_idx=0):
        super(TransformerEncoderOnly, self).__init__()
        
        self.d_model = d_model
        self.vocab_size = vocab_size
        
        # Embeddings
        self.embedding = nn.Embedding(vocab_size, d_model, padding_idx=padding_idx)
        self.positional_encoding = PositionalEncoding(d_model, max_seq_len, dropout)
        
        # Encoder
        self.encoder = TransformerEncoder(
            d_model, num_heads, d_ff, num_layers, dropout
        )
        
        # Classification head
        self.dropout = nn.Dropout(dropout)
        self.classifier = nn.Linear(d_model, num_classes)
        
        # Initialize weights
        self._init_weights()
    
    def _init_weights(self):
        """Initialize model weights."""
        for p in self.parameters():
            if p.dim() > 1:
                nn.init.xavier_uniform_(p)
    
    def forward(self, input_ids, attention_mask=None):
        """
        Args:
            input_ids: Token IDs (batch_size, seq_len)
            attention_mask: Attention mask
        
        Returns:
            logits: Classification logits (batch_size, num_classes)
        """
        # Embedding and positional encoding
        embed = self.embedding(input_ids) * (self.d_model ** 0.5)
        embed = self.positional_encoding(embed)
        
        # Encode
        encoded = self.encoder(embed, attention_mask)
        
        # Use [CLS] token (first token) for classification
        cls_output = encoded[:, 0, :]
        
        # Classification
        logits = self.classifier(self.dropout(cls_output))
        
        return logits


if __name__ == "__main__":
    print("Testing Full Transformer:")
    vocab_size = 10000
    d_model = 512
    num_heads = 8
    d_ff = 2048
    
    model = Transformer(vocab_size, d_model, num_heads, d_ff)
    
    batch_size = 2
    src_seq_len = 10
    tgt_seq_len = 8
    
    src = torch.randint(0, vocab_size, (batch_size, src_seq_len))
    tgt = torch.randint(0, vocab_size, (batch_size, tgt_seq_len))
    
    # Create causal mask for decoder
    tgt_mask = create_causal_mask(tgt_seq_len, tgt.device)
    
    logits = model(src, tgt, tgt_mask=tgt_mask)
    
    print(f"Source shape: {src.shape}")
    print(f"Target shape: {tgt.shape}")
    print(f"Output logits shape: {logits.shape}")
    print()
    
    print("Testing Transformer Encoder Only:")
    encoder_model = TransformerEncoderOnly(vocab_size, d_model, num_heads, 
                                          d_ff, num_classes=2)
    
    input_ids = torch.randint(0, vocab_size, (batch_size, 20))
    logits = encoder_model(input_ids)
    
    print(f"Input shape: {input_ids.shape}")
    print(f"Output logits shape: {logits.shape}")
