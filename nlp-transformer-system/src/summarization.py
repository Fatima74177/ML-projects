"""Text summarization using pre-trained models."""
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM


class Summarizer:
    """Text summarization using T5 and BART models."""
    
    def __init__(self, model_name="google-t5/t5-small"):
        """
        Initialize summarizer.
        
        Args:
            model_name: Pretrained model name from Hugging Face Hub
        """
        self.model_name = model_name
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.model.eval()
    
    def summarize(self, text, min_length=50, max_length=150, num_beams=4):
        """
        Summarize text.
        
        Args:
            text: Input text to summarize
            min_length: Minimum summary length
            max_length: Maximum summary length
            num_beams: Number of beams for beam search
        
        Returns:
            Summary text
        """
        # Tokenize
        if self.model.config.model_type == "t5" and not text.startswith("summarize: "):
            text = f"summarize: {text}"
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Generate summary
        with torch.no_grad():
            summary_ids = self.model.generate(
                inputs['input_ids'],
                attention_mask=inputs['attention_mask'],
                min_length=min_length,
                max_length=max_length,
                num_beams=num_beams,
                early_stopping=True,
                length_penalty=2.0,
                no_repeat_ngram_size=3,
            )
        
        # Decode
        summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        return summary
    
    def summarize_batch(self, texts, min_length=50, max_length=150):
        """
        Summarize multiple texts.
        
        Args:
            texts: List of input texts
            min_length: Minimum summary length
            max_length: Maximum summary length
        
        Returns:
            List of summaries
        """
        summaries = []
        for text in texts:
            summary = self.summarize(text, min_length, max_length)
            summaries.append(summary)
        return summaries


class SummarizerPipeline:
    """High-level summarization wrapper compatible with Transformers 4 and 5."""
    
    def __init__(self, model_name="google-t5/t5-small"):
        """Initialize summarization pipeline."""
        # Transformers 5 removed the legacy ``summarization`` pipeline task.
        # Use the underlying sequence-to-sequence model directly instead.
        self.summarizer = Summarizer(model_name)
    
    def summarize(self, text, min_length=50, max_length=150):
        """Summarize text using pipeline."""
        return self.summarizer.summarize(
            text, min_length=min_length, max_length=max_length
        )
    
    def summarize_batch(self, texts, min_length=50, max_length=150):
        """Summarize multiple texts."""
        return self.summarizer.summarize_batch(
            texts, min_length=min_length, max_length=max_length
        )


# Example usage and testing
if __name__ == "__main__":
    print("Testing Text Summarization:")
    print("="*60)
    
    article = """
    Artificial intelligence is transforming the world in unprecedented ways. 
    From healthcare to finance, AI systems are being deployed to solve complex problems 
    and improve decision-making. Machine learning algorithms can now process vast amounts 
    of data and identify patterns that would be impossible for humans to detect manually.
    
    Deep learning models, particularly neural networks with many layers, have achieved 
    remarkable success in various domains. Natural language processing has seen dramatic 
    improvements with transformer models like BERT and GPT. Computer vision systems can 
    now recognize objects with accuracy exceeding human performance.
    
    However, AI also brings challenges. Concerns about bias, privacy, and job displacement 
    are important considerations. Ensuring that AI systems are fair, transparent, and 
    beneficial to society requires careful research and thoughtful regulation.
    
    The future of AI depends on responsible development and deployment. By addressing 
    these challenges proactively, we can harness the potential of AI while minimizing risks.
    """
    
    try:
        summarizer = SummarizerPipeline()
        
        print("Original Text:")
        print(article[:200] + "...")
        print("\n" + "="*60)
        
        summary_short = summarizer.summarize(article, min_length=30, max_length=80)
        print("\nShort Summary (max 80 tokens):")
        print(summary_short)
        
        summary_medium = summarizer.summarize(article, min_length=50, max_length=150)
        print("\nMedium Summary (max 150 tokens):")
        print(summary_medium)
        
        summary_long = summarizer.summarize(article, min_length=80, max_length=250)
        print("\nLong Summary (max 250 tokens):")
        print(summary_long)
        
    except Exception as e:
        print(f"Error: {e}")
        print("Note: Summarization requires the google-t5/t5-small model")
