"""Named Entity Recognition (NER) using pre-trained models."""
import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
import numpy as np


class NERAnalyzer:
    """Named Entity Recognition using Hugging Face transformers."""
    
    def __init__(self, model_name="dslim/distilbert-NER"):
        """
        Initialize NER analyzer.
        
        Args:
            model_name: Pretrained model name from Hugging Face Hub
        """
        self.model_name = model_name
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForTokenClassification.from_pretrained(model_name)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.model.eval()
        
        # Label mapping
        self.id2label = self.model.config.id2label
        self.label2id = {v: k for k, v in self.id2label.items()}
    
    def predict(self, text):
        """
        Predict entities for a text.
        
        Args:
            text: Input text
        
        Returns:
            List of entities with their types and positions
        """
        # Tokenize
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        input_ids = inputs['input_ids']
        
        # Move to device
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Forward pass
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
        
        # Get predictions
        predictions = logits.argmax(dim=-1)[0].cpu().numpy()
        
        # Get tokens
        tokens = self.tokenizer.convert_ids_to_tokens(input_ids[0])
        
        # Extract entities
        entities = []
        current_entity = None
        
        for token, pred_id in zip(tokens, predictions):
            label = self.id2label[pred_id]
            
            # Skip special tokens
            if label == 'O' or token.startswith('['):
                if current_entity:
                    entities.append(current_entity)
                    current_entity = None
                continue
            
            # Handle B- and I- tags
            if label.startswith('B-'):
                if current_entity:
                    entities.append(current_entity)
                entity_type = label[2:]  # Remove B- prefix
                current_entity = {
                    'text': token,
                    'type': entity_type,
                    'confidence': 0.0
                }
            elif label.startswith('I-') and current_entity:
                entity_type = label[2:]  # Remove I- prefix
                if current_entity['type'] == entity_type:
                    # Combine subword tokens
                    if token.startswith('##'):
                        current_entity['text'] += token[2:]
                    else:
                        current_entity['text'] += ' ' + token
        
        if current_entity:
            entities.append(current_entity)
        
        return {
            'text': text,
            'entities': entities
        }
    
    def predict_batch(self, texts):
        """
        Predict entities for multiple texts.
        
        Args:
            texts: List of input texts
        
        Returns:
            List of predictions
        """
        results = []
        for text in texts:
            results.append(self.predict(text))
        return results
    
    def get_entity_types(self):
        """Get list of entity types."""
        entity_types = set()
        for label in self.id2label.values():
            if label != 'O' and label.startswith('B-'):
                entity_types.add(label[2:])
        return sorted(list(entity_types))


class NERPipeline:
    """High-level NER pipeline."""
    
    def __init__(self, model_name="dslim/distilbert-NER"):
        """Initialize NER pipeline."""
        self.pipeline = pipeline(
            "ner",
            model=model_name,
            aggregation_strategy="simple",
            device=0 if torch.cuda.is_available() else -1
        )
    
    def predict(self, text):
        """Predict entities using pipeline."""
        entities = self.pipeline(text)
        out_entities = []
        for entity in entities:
            # Some pipeline versions may return non-dict entries; guard accordingly
            if isinstance(entity, dict):
                # Flexible key handling: different transformers versions use
                # 'entity', 'entity_group', or 'label' for the predicted type.
                ent_text = entity.get('word') or entity.get('text') or entity.get('entity') or ''
                ent_text = str(ent_text).replace(' ##', '')
                ent_type = (
                    entity.get('entity')
                    or entity.get('entity_group')
                    or entity.get('label')
                    or entity.get('entity_type')
                    or 'UNKNOWN'
                )
                ent_score = entity.get('score') or entity.get('confidence') or 0.0
            else:
                ent_text = str(entity)
                ent_type = 'UNKNOWN'
                ent_score = 0.0

            out_entities.append({'text': ent_text, 'type': ent_type, 'confidence': ent_score})

        return {
            'text': text,
            'entities': out_entities
        }
    
    def predict_batch(self, texts):
        """Predict entities for batch of texts."""
        results = []
        for text in texts:
            results.append(self.predict(text))
        return results


def format_ner_results(result):
    """Format NER results for display."""
    text = result['text']
    entities = result['entities']
    
    output = f"Text: {text}\n"
    output += "Entities:\n"
    
    if not entities:
        output += "  No entities found\n"
    else:
        for entity in entities:
            output += f"  - {entity['text']}: {entity['type']}"
            if 'confidence' in entity:
                output += f" ({entity['confidence']:.4f})"
            output += "\n"
    
    return output


# Example usage and testing
if __name__ == "__main__":
    print("Testing NER Analysis:")
    print("="*60)
    
    # Using NERPipeline
    analyzer = NERPipeline()
    
    texts = [
        "Elon Musk founded Tesla in California.",
        "Barack Obama was the 44th President of the United States.",
        "Apple Inc. is headquartered in Cupertino, California.",
        "John works at Google in Mountain View.",
    ]
    
    print("NER Predictions:")
    for text in texts:
        result = analyzer.predict(text)
        print(format_ner_results(result))
        print()
    
    print("="*60)
    print("Batch Predictions:")
    results = analyzer.predict_batch(texts)
    for result in results:
        print(format_ner_results(result))
        print()
