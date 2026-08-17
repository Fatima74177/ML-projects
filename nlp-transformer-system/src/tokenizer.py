"""Tokenization utilities for NLP."""
import json
from collections import Counter, defaultdict
from transformers import AutoTokenizer


class SimpleBPETokenizer:
    """Simple Byte Pair Encoding (BPE) tokenizer implementation."""
    
    def __init__(self, vocab_size=10000, num_merges=1000):
        self.vocab_size = vocab_size
        self.num_merges = num_merges
        self.vocab = {}
        self.merges = []
        self.token_to_id = {}
        self.id_to_token = {}
    
    def build_vocab(self, texts):
        """Build vocabulary from texts."""
        # Initialize vocab with characters
        vocab = Counter()
        for text in texts:
            words = text.split()
            for word in words:
                vocab[' '.join(list(word)) + ' </w>'] += 1
        
        self.vocab = vocab
        self._build_token_mappings()
    
    def _build_token_mappings(self):
        """Build token-to-id and id-to-token mappings."""
        tokens = sorted(set(' '.join(self.vocab.keys()).split()))
        self.token_to_id = {token: idx for idx, token in enumerate(tokens)}
        self.id_to_token = {idx: token for token, idx in self.token_to_id.items()}
    
    def encode(self, text):
        """Encode text to token IDs."""
        words = text.split()
        tokens = []
        for word in words:
            word_tokens = list(word) + ['</w>']
            token_ids = [self.token_to_id.get(t, self.token_to_id.get('[UNK]', 0)) 
                        for t in word_tokens]
            tokens.extend(token_ids)
        return tokens
    
    def decode(self, token_ids):
        """Decode token IDs back to text."""
        tokens = [self.id_to_token.get(tid, '[UNK]') for tid in token_ids]
        text = ''.join(tokens).replace('</w>', ' ').strip()
        return text


class TokenizerWrapper:
    """Wrapper for Hugging Face pretrained tokenizers."""
    
    def __init__(self, model_name="bert-base-uncased"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model_name = model_name
    
    def encode(self, text, max_length=512, padding=True, truncation=True, return_tensors=None):
        """Encode text using pretrained tokenizer."""
        encoding = self.tokenizer(
            text,
            max_length=max_length,
            padding=padding if padding else False,
            truncation=truncation if truncation else False,
            return_tensors=return_tensors
        )
        return encoding
    
    def decode(self, token_ids, skip_special_tokens=True):
        """Decode token IDs back to text."""
        return self.tokenizer.decode(token_ids, skip_special_tokens=skip_special_tokens)
    
    def get_vocab_size(self):
        """Get vocabulary size."""
        return len(self.tokenizer)
    
    def get_special_tokens(self):
        """Get special tokens."""
        return {
            'cls_token': self.tokenizer.cls_token,
            'sep_token': self.tokenizer.sep_token,
            'pad_token': self.tokenizer.pad_token,
            'unk_token': self.tokenizer.unk_token,
            'mask_token': self.tokenizer.mask_token,
        }


def create_tokenizer(tokenizer_type="pretrained", model_name="bert-base-uncased", **kwargs):
    """Factory function to create a tokenizer."""
    if tokenizer_type == "pretrained":
        return TokenizerWrapper(model_name)
    elif tokenizer_type == "bpe":
        return SimpleBPETokenizer(**kwargs)
    else:
        raise ValueError(f"Unknown tokenizer type: {tokenizer_type}")


# Example usage and testing
if __name__ == "__main__":
    # Test pretrained tokenizer
    print("Testing Pretrained BERT Tokenizer:")
    tokenizer = create_tokenizer("pretrained", "bert-base-uncased")
    text = "Hello, this is a test sentence for tokenization."
    encoding = tokenizer.encode(text)
    print(f"Input: {text}")
    print(f"Tokens: {encoding['input_ids']}")
    print(f"Attention mask: {encoding['attention_mask']}")
    decoded = tokenizer.decode(encoding['input_ids'])
    print(f"Decoded: {decoded}")
    print(f"Vocab size: {tokenizer.get_vocab_size()}")
    print()
    
    # Test BPE tokenizer
    print("Testing Simple BPE Tokenizer:")
    texts = ["hello world", "this is a test"]
    bpe_tokenizer = create_tokenizer("bpe", vocab_size=1000, num_merges=100)
    bpe_tokenizer.build_vocab(texts)
    test_text = "hello world"
    encoded = bpe_tokenizer.encode(test_text)
    print(f"Input: {test_text}")
    print(f"Encoded: {encoded}")
    decoded = bpe_tokenizer.decode(encoded)
    print(f"Decoded: {decoded}")
