"""Sentiment analysis using pre-trained models."""
import torch
import torch.nn as nn
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import numpy as np


class SentimentAnalyzer:
    """Sentiment analysis using Hugging Face transformers."""
    
    def __init__(self, model_name="distilbert-base-uncased-finetuned-sst-2-english"):
        """
        Initialize sentiment analyzer.
        
        Args:
            model_name: Pretrained model name from Hugging Face Hub
        """
        self.model_name = model_name
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.model.eval()
        
        # Label mapping
        self.id2label = self.model.config.id2label
        self.label2id = {v: k for k, v in self.id2label.items()}
    
    def predict(self, text, return_probabilities=False):
        """
        Predict sentiment for a single text.
        
        Args:
            text: Input text
            return_probabilities: Whether to return probability scores
        
        Returns:
            dict with sentiment and confidence
        """
        # Tokenize
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Forward pass
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
        
        # Get prediction
        predicted_class_id = logits.argmax().item()
        predicted_label = self.id2label[predicted_class_id]
        
        # Get confidence
        probs = torch.softmax(logits, dim=-1)
        confidence = probs[0, predicted_class_id].item()
        
        result = {
            'text': text,
            'sentiment': predicted_label,
            'confidence': confidence,
            'predicted_class_id': predicted_class_id
        }
        
        if return_probabilities:
            result['probabilities'] = {
                self.id2label[i]: probs[0, i].item() 
                for i in range(len(self.id2label))
            }
        
        return result
    
    def predict_batch(self, texts, return_probabilities=False):
        """
        Predict sentiment for multiple texts.
        
        Args:
            texts: List of input texts
            return_probabilities: Whether to return probability scores
        
        Returns:
            List of predictions
        """
        results = []
        for text in texts:
            results.append(self.predict(text, return_probabilities))
        return results
    
    def fine_tune(self, train_dataset, val_dataset, num_epochs=3, batch_size=16, 
                  learning_rate=2e-5):
        """
        Fine-tune the model on a custom dataset.
        
        Args:
            train_dataset: Training dataset
            val_dataset: Validation dataset
            num_epochs: Number of training epochs
            batch_size: Batch size
            learning_rate: Learning rate
        
        Returns:
            Training history
        """
        from torch.utils.data import DataLoader
        from transformers import AdamW
        
        # Create data loaders
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=batch_size)
        
        # Optimizer
        optimizer = AdamW(self.model.parameters(), lr=learning_rate)
        
        # Training loop
        history = {'train_loss': [], 'val_loss': [], 'val_accuracy': []}
        
        for epoch in range(num_epochs):
            # Training
            self.model.train()
            train_loss = 0
            for batch in train_loader:
                inputs = {k: v.to(self.device) for k, v in batch.items()}
                
                optimizer.zero_grad()
                outputs = self.model(**inputs)
                loss = outputs.loss
                
                loss.backward()
                optimizer.step()
                
                train_loss += loss.item()
            
            train_loss /= len(train_loader)
            history['train_loss'].append(train_loss)
            
            # Validation
            self.model.eval()
            val_loss = 0
            correct = 0
            total = 0
            
            with torch.no_grad():
                for batch in val_loader:
                    inputs = {k: v.to(self.device) for k, v in batch.items()}
                    labels = inputs['labels']
                    
                    outputs = self.model(**inputs)
                    loss = outputs.loss
                    val_loss += loss.item()
                    
                    preds = outputs.logits.argmax(dim=-1)
                    correct += (preds == labels).sum().item()
                    total += labels.size(0)
            
            val_loss /= len(val_loader)
            val_accuracy = correct / total
            
            history['val_loss'].append(val_loss)
            history['val_accuracy'].append(val_accuracy)
            
            print(f"Epoch {epoch+1}/{num_epochs}")
            print(f"  Train Loss: {train_loss:.4f}")
            print(f"  Val Loss: {val_loss:.4f}")
            print(f"  Val Accuracy: {val_accuracy:.4f}")
        
        return history
    
    def save(self, path):
        """Save model and tokenizer."""
        self.model.save_pretrained(path)
        self.tokenizer.save_pretrained(path)
        print(f"Model saved to {path}")
    
    def load(self, path):
        """Load model and tokenizer."""
        self.model = AutoModelForSequenceClassification.from_pretrained(path)
        self.tokenizer = AutoTokenizer.from_pretrained(path)
        self.model.to(self.device)
        self.model.eval()
        print(f"Model loaded from {path}")


class SentimentPipeline:
    """High-level sentiment analysis pipeline."""
    
    def __init__(self, model_name="distilbert-base-uncased-finetuned-sst-2-english"):
        """Initialize pipeline using Hugging Face pipeline."""
        self.pipeline = pipeline(
            "sentiment-analysis",
            model=model_name,
            device=0 if torch.cuda.is_available() else -1
        )
    
    def predict(self, text):
        """Predict sentiment using pipeline."""
        result = self.pipeline(text)[0]
        return {
            'text': text,
            'sentiment': result['label'],
            'confidence': result['score']
        }
    
    def predict_batch(self, texts):
        """Predict sentiments for batch of texts."""
        results = self.pipeline(texts)
        return [
            {
                'text': text,
                'sentiment': result['label'],
                'confidence': result['score']
            }
            for text, result in zip(texts, results)
        ]


# Example usage and testing
if __name__ == "__main__":
    print("Testing Sentiment Analysis:")
    
    # Using SentimentAnalyzer
    analyzer = SentimentAnalyzer()
    
    # Single prediction
    texts = [
        "I absolutely loved this movie! It was fantastic.",
        "This was a terrible experience. I hated it.",
        "It was okay, nothing special.",
    ]
    
    print("Single Predictions:")
    for text in texts:
        result = analyzer.predict(text, return_probabilities=True)
        print(f"\nText: {result['text']}")
        print(f"Sentiment: {result['sentiment']}")
        print(f"Confidence: {result['confidence']:.4f}")
        print(f"Probabilities: {result['probabilities']}")
    
    print("\n" + "="*60)
    print("Batch Predictions:")
    results = analyzer.predict_batch(texts)
    for result in results:
        print(f"Text: {result['text']}")
        print(f"Sentiment: {result['sentiment']} ({result['confidence']:.4f})")
        print()
    
    # Using SentimentPipeline
    print("\n" + "="*60)
    print("Using Sentiment Pipeline:")
    pipeline = SentimentPipeline()
    for text in texts:
        result = pipeline.predict(text)
        print(f"Text: {result['text']}")
        print(f"Sentiment: {result['sentiment']} ({result['confidence']:.4f})")
        print()
