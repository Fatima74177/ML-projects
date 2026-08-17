"""Text generation using pre-trained language models."""
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import numpy as np


class TextGenerator:
    """Text generation using GPT-like models."""
    
    def __init__(self, model_name="gpt2"):
        """
        Initialize text generator.
        
        Args:
            model_name: Pretrained model name from Hugging Face Hub
        """
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self.load_error = None
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForCausalLM.from_pretrained(model_name)
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.model.to(self.device)
            self.model.eval()
        except Exception as exc:
            self.load_error = str(exc)
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Set pad token
        if self.tokenizer is not None and self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
    
    def generate_greedy(self, prompt, max_length=100, temperature=1.0):
        """
        Generate text using greedy decoding (always select highest probability token).
        
        Args:
            prompt: Starting prompt
            max_length: Maximum length of generated text
            temperature: Softmax temperature for controlling randomness
        
        Returns:
            Generated text
        """
        if self.model is None or self.tokenizer is None:
            return self._fallback_generation(prompt, reason=self.load_error or "model is unavailable")

        inputs = self.tokenizer(prompt, return_tensors="pt")
        input_ids = inputs['input_ids'].to(self.device)
        attention_mask = inputs['attention_mask'].to(self.device)
        
        with torch.no_grad():
            for _ in range(max_length):
                outputs = self.model(input_ids, attention_mask=attention_mask)
                logits = outputs.logits[0, -1, :]
                
                # Apply temperature
                if temperature != 1.0:
                    logits = logits / temperature
                
                # Get next token (greedy)
                next_token_id = logits.argmax().unsqueeze(0).unsqueeze(0)
                
                input_ids = torch.cat([input_ids, next_token_id], dim=-1)
                attention_mask = torch.cat(
                    [attention_mask, torch.ones((1, 1), device=self.device)],
                    dim=-1
                )
                
                # Stop if EOS token
                if next_token_id.item() == self.tokenizer.eos_token_id:
                    break
        
        return self.tokenizer.decode(input_ids[0], skip_special_tokens=True)
    
    def generate_topk(self, prompt, max_length=100, k=50, temperature=1.0):
        """
        Generate text using top-k sampling.
        
        Only samples from the k most likely next tokens.
        
        Args:
            prompt: Starting prompt
            max_length: Maximum length of generated text
            k: Number of top tokens to consider
            temperature: Softmax temperature
        
        Returns:
            Generated text
        """
        if self.model is None or self.tokenizer is None:
            return self._fallback_generation(prompt, reason=self.load_error or "model is unavailable")

        inputs = self.tokenizer(prompt, return_tensors="pt")
        input_ids = inputs['input_ids'].to(self.device)
        attention_mask = inputs['attention_mask'].to(self.device)
        
        with torch.no_grad():
            for _ in range(max_length):
                outputs = self.model(input_ids, attention_mask=attention_mask)
                logits = outputs.logits[0, -1, :]
                
                # Apply temperature
                if temperature != 1.0:
                    logits = logits / temperature
                
                # Get top-k
                top_k_logits, top_k_indices = torch.topk(logits, k)
                
                # Apply softmax
                top_k_probs = F.softmax(top_k_logits, dim=-1)
                
                # Sample
                sampled_idx = torch.multinomial(top_k_probs, 1)
                next_token_id = top_k_indices[sampled_idx].unsqueeze(0)
                
                input_ids = torch.cat([input_ids, next_token_id], dim=-1)
                attention_mask = torch.cat(
                    [attention_mask, torch.ones((1, 1), device=self.device)],
                    dim=-1
                )
                
                if next_token_id.item() == self.tokenizer.eos_token_id:
                    break
        
        return self.tokenizer.decode(input_ids[0], skip_special_tokens=True)
    
    def generate_nucleus(self, prompt, max_length=100, p=0.9, temperature=1.0):
        """
        Generate text using nucleus (top-p) sampling.
        
        Samples from the smallest set of tokens whose cumulative probability exceeds p.
        
        Args:
            prompt: Starting prompt
            max_length: Maximum length of generated text
            p: Cumulative probability threshold
            temperature: Softmax temperature
        
        Returns:
            Generated text
        """
        if self.model is None or self.tokenizer is None:
            return self._fallback_generation(prompt, reason=self.load_error or "model is unavailable")

        inputs = self.tokenizer(prompt, return_tensors="pt")
        input_ids = inputs['input_ids'].to(self.device)
        attention_mask = inputs['attention_mask'].to(self.device)
        
        with torch.no_grad():
            for _ in range(max_length):
                outputs = self.model(input_ids, attention_mask=attention_mask)
                logits = outputs.logits[0, -1, :]
                
                # Apply temperature
                if temperature != 1.0:
                    logits = logits / temperature
                
                # Get probabilities
                probs = F.softmax(logits, dim=-1)
                
                # Sort probabilities
                sorted_probs, sorted_indices = torch.sort(probs, descending=True)
                
                # Get cumulative probabilities
                cumsum_probs = torch.cumsum(sorted_probs, dim=-1)
                
                # Get top-p tokens
                mask = cumsum_probs <= p
                mask[0] = True  # Always keep at least one token
                
                # Sample
                top_p_probs = sorted_probs[mask]
                top_p_probs = top_p_probs / top_p_probs.sum()
                
                sampled_idx = torch.multinomial(top_p_probs, 1)
                next_token_id = sorted_indices[mask][sampled_idx].unsqueeze(0)
                
                input_ids = torch.cat([input_ids, next_token_id], dim=-1)
                attention_mask = torch.cat(
                    [attention_mask, torch.ones((1, 1), device=self.device)],
                    dim=-1
                )
                
                if next_token_id.item() == self.tokenizer.eos_token_id:
                    break
        
        return self.tokenizer.decode(input_ids[0], skip_special_tokens=True)
    
    def generate_beam_search(self, prompt, max_length=100, num_beams=5):
        """
        Generate text using beam search.
        
        Maintains multiple hypotheses to find a high-probability sequence.
        
        Args:
            prompt: Starting prompt
            max_length: Maximum length of generated text
            num_beams: Number of beams to maintain
        
        Returns:
            Generated text
        """
        if self.model is None or self.tokenizer is None:
            return self._fallback_generation(prompt, reason=self.load_error or "model is unavailable")

        inputs = self.tokenizer(prompt, return_tensors="pt")
        input_ids = inputs['input_ids'].to(self.device)
        
        with torch.no_grad():
            output = self.model.generate(
                input_ids,
                max_length=max_length,
                num_beams=num_beams,
                no_repeat_ngram_size=2,
                early_stopping=True
            )
        
        return self.tokenizer.decode(output[0], skip_special_tokens=True)

    def _fallback_generation(self, prompt, reason="model is unavailable"):
        """Provide a non-crashing fallback when a model cannot be loaded."""
        # Return a demo message + continuation
        demo_continuations = [
            " is the key to success in modern machine learning systems.",
            " enables efficient processing of natural language data.",
            " represents a significant advancement in artificial intelligence.",
            " has revolutionized how we approach computational problems.",
            " demonstrates the power of deep learning architectures.",
            " showcases the importance of transformer-based models.",
        ]
        continuation = demo_continuations[hash(prompt) % len(demo_continuations)]
        return f"{prompt}{continuation}\n\n[Note: Running in demo mode—GPT-2 model unavailable. Reason: {reason}]"
    
    def generate(self, prompt, method="nucleus", max_length=100, **kwargs):
        """
        Generate text using specified method.
        
        Args:
            prompt: Starting prompt
            method: Generation method ("greedy", "topk", "nucleus", "beam_search")
            max_length: Maximum length of generated text
            **kwargs: Additional arguments for the generation method
        
        Returns:
            Generated text
        """
        if method == "greedy":
            return self.generate_greedy(prompt, max_length, **kwargs)
        elif method == "topk":
            return self.generate_topk(prompt, max_length, **kwargs)
        elif method == "nucleus":
            return self.generate_nucleus(prompt, max_length, **kwargs)
        elif method == "beam_search":
            return self.generate_beam_search(prompt, max_length, **kwargs)
        else:
            raise ValueError(f"Unknown generation method: {method}")


class GenerationPipeline:
    """High-level text generation pipeline."""
    
    def __init__(self, model_name="gpt2"):
        """Initialize generation pipeline."""
        self.pipeline = pipeline(
            "text-generation",
            model=model_name,
            device=0 if torch.cuda.is_available() else -1
        )
    
    def generate(self, prompt, max_length=100, num_return_sequences=1):
        """Generate text using pipeline."""
        results = self.pipeline(
            prompt,
            max_length=max_length,
            num_return_sequences=num_return_sequences,
            do_sample=True,
            temperature=0.7,
            top_k=50,
            top_p=0.95
        )
        return results


# Example usage and testing
if __name__ == "__main__":
    print("Testing Text Generation:")
    print("="*60)
    
    generator = TextGenerator("gpt2")
    
    prompts = [
        "Artificial intelligence will",
        "The future of technology",
        "Machine learning models are",
    ]
    
    methods = ["greedy", "topk", "nucleus", "beam_search"]
    
    for prompt in prompts:
        print(f"\nPrompt: {prompt}")
        print("-" * 60)
        
        for method in methods:
            try:
                if method == "greedy":
                    result = generator.generate(prompt, method=method, max_length=50, temperature=0.7)
                elif method == "topk":
                    result = generator.generate(prompt, method=method, max_length=50, k=50, temperature=0.7)
                elif method == "nucleus":
                    result = generator.generate(prompt, method=method, max_length=50, p=0.9, temperature=0.7)
                else:
                    result = generator.generate(prompt, method=method, max_length=50)
                
                print(f"\n{method.upper()}:")
                print(result)
            except Exception as e:
                print(f"{method.upper()}: Error - {e}")
        
        print()
