"""Model evaluation metrics and utilities."""
import numpy as np
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, roc_auc_score, roc_curve
)
from sklearn.preprocessing import label_binarize


class ClassificationMetrics:
    """Compute metrics for classification tasks."""
    
    def __init__(self, y_true, y_pred, y_pred_proba=None, labels=None):
        """
        Initialize metrics calculator.
        
        Args:
            y_true: True labels
            y_pred: Predicted labels
            y_pred_proba: Predicted probabilities (for binary/multiclass)
            labels: List of label names
        """
        self.y_true = y_true
        self.y_pred = y_pred
        self.y_pred_proba = y_pred_proba
        self.labels = labels
    
    def accuracy(self):
        """Calculate accuracy."""
        return accuracy_score(self.y_true, self.y_pred)
    
    def precision(self, average='weighted'):
        """Calculate precision."""
        return precision_score(self.y_true, self.y_pred, average=average, zero_division=0)
    
    def recall(self, average='weighted'):
        """Calculate recall."""
        return recall_score(self.y_true, self.y_pred, average=average, zero_division=0)
    
    def f1(self, average='weighted'):
        """Calculate F1 score."""
        return f1_score(self.y_true, self.y_pred, average=average, zero_division=0)
    
    def confusion_matrix_scores(self):
        """Get confusion matrix."""
        return confusion_matrix(self.y_true, self.y_pred)
    
    def classification_report(self):
        """Get detailed classification report."""
        return classification_report(
            self.y_true, self.y_pred,
            target_names=self.labels,
            zero_division=0
        )
    
    def get_metrics_dict(self):
        """Get all metrics as a dictionary."""
        return {
            'accuracy': self.accuracy(),
            'precision': self.precision(),
            'recall': self.recall(),
            'f1': self.f1(),
        }
    
    def plot_confusion_matrix(self, figsize=(10, 8)):
        """Plot confusion matrix."""
        cm = self.confusion_matrix_scores()
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns
        except Exception as e:
            raise ImportError("plot_confusion_matrix requires matplotlib and seaborn installed") from e

        plt.figure(figsize=figsize)
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', cbar=True)

        if self.labels:
            plt.xticks(range(len(self.labels)), self.labels, rotation=45)
            plt.yticks(range(len(self.labels)), self.labels, rotation=0)

        plt.xlabel('Predicted')
        plt.ylabel('True')
        plt.title('Confusion Matrix')
        plt.tight_layout()
        return plt
    
    def plot_metrics(self, figsize=(10, 6)):
        """Plot metrics as bar chart."""
        metrics = self.get_metrics_dict()
        try:
            import matplotlib.pyplot as plt
        except Exception as e:
            raise ImportError("plot_metrics requires matplotlib installed") from e

        plt.figure(figsize=figsize)
        plt.bar(metrics.keys(), metrics.values())
        plt.ylim([0, 1])
        plt.ylabel('Score')
        plt.title('Classification Metrics')
        plt.xticks(rotation=45)

        # Add value labels on bars
        for i, (k, v) in enumerate(metrics.items()):
            plt.text(i, v + 0.02, f'{v:.3f}', ha='center')

        plt.tight_layout()
        return plt


class GenerationMetrics:
    """Compute metrics for text generation tasks."""
    
    @staticmethod
    def calculate_bleu(reference, hypothesis, n_gram=4):
        """
        Calculate BLEU score (simplified version).
        
        Args:
            reference: Reference text
            hypothesis: Generated text
            n_gram: Maximum n-gram size
        
        Returns:
            BLEU score
        """
        from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
        
        ref_tokens = reference.lower().split()
        hyp_tokens = hypothesis.lower().split()
        
        # Create n-gram references
        ref_list = [ref_tokens]
        
        # Calculate BLEU
        smoothing_function = SmoothingFunction().method1
        bleu_score = sentence_bleu(
            ref_list, hyp_tokens,
            weights=[1/n_gram] * n_gram,
            smoothing_function=smoothing_function
        )
        
        return bleu_score
    
    @staticmethod
    def calculate_rouge(reference, hypothesis):
        """
        Calculate ROUGE score (simplified version).
        
        Args:
            reference: Reference text
            hypothesis: Generated text
        
        Returns:
            ROUGE-L F1 score
        """
        ref_tokens = set(reference.lower().split())
        hyp_tokens = set(hypothesis.lower().split())
        
        # Calculate intersection
        intersection = ref_tokens & hyp_tokens
        
        # Calculate precision and recall
        precision = len(intersection) / len(hyp_tokens) if hyp_tokens else 0
        recall = len(intersection) / len(ref_tokens) if ref_tokens else 0
        
        # Calculate F1
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) else 0
        
        return f1
    
    @staticmethod
    def calculate_perplexity(loss):
        """
        Calculate perplexity from loss.
        
        Perplexity = exp(loss)
        
        Args:
            loss: Cross-entropy loss
        
        Returns:
            Perplexity score
        """
        return np.exp(loss)


class NERMetrics:
    """Compute metrics for NER tasks."""
    
    @staticmethod
    def calculate_entity_metrics(true_entities, pred_entities):
        """
        Calculate entity-level metrics.
        
        Args:
            true_entities: List of true entities
            pred_entities: List of predicted entities
        
        Returns:
            Precision, recall, F1 score
        """
        true_set = set(true_entities)
        pred_set = set(pred_entities)
        
        # Intersection (correct predictions)
        correct = true_set & pred_set
        
        # Precision: correct / predicted
        precision = len(correct) / len(pred_set) if pred_set else 0
        
        # Recall: correct / true
        recall = len(correct) / len(true_set) if true_set else 0
        
        # F1 score
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) else 0
        
        return {
            'precision': precision,
            'recall': recall,
            'f1': f1,
        }


class ModelComparison:
    """Compare multiple models."""
    
    def __init__(self):
        self.results = {}
    
    def add_result(self, model_name, metrics):
        """
        Add model result.
        
        Args:
            model_name: Name of the model
            metrics: Dictionary of metrics
        """
        self.results[model_name] = metrics
    
    def compare(self):
        """Compare models across metrics."""
        if not self.results:
            return None
        
        # Create comparison table
        metrics_names = set()
        for metrics in self.results.values():
            metrics_names.update(metrics.keys())
        
        comparison = {}
        for metric in sorted(metrics_names):
            comparison[metric] = {}
            for model, metrics in self.results.items():
                comparison[metric][model] = metrics.get(metric, None)
        
        return comparison
    
    def plot_comparison(self, figsize=(12, 6)):
        """Plot model comparison."""
        if not self.results:
            return None
        
        # Create comparison matrix
        metrics_names = set()
        for metrics in self.results.values():
            metrics_names.update(metrics.keys())
        
        model_names = list(self.results.keys())
        metrics_names = sorted(list(metrics_names))
        
        # Create data for plotting
        data = np.zeros((len(model_names), len(metrics_names)))
        for i, model in enumerate(model_names):
            for j, metric in enumerate(metrics_names):
                data[i, j] = self.results[model].get(metric, 0)
        
        try:
            import matplotlib.pyplot as plt
        except Exception as e:
            raise ImportError("plot_comparison requires matplotlib installed") from e

        # Plot
        fig, axes = plt.subplots(1, len(metrics_names), figsize=figsize)

        if len(metrics_names) == 1:
            axes = [axes]

        for j, metric in enumerate(metrics_names):
            axes[j].bar(model_names, data[:, j])
            axes[j].set_title(metric)
            axes[j].set_ylim([0, 1])
            axes[j].tick_params(axis='x', rotation=45)

        plt.tight_layout()
        return plt


# Example usage and testing
if __name__ == "__main__":
    print("Testing Evaluation Metrics:")
    print("="*60)
    
    # Test classification metrics
    print("Classification Metrics:")
    y_true = [0, 1, 0, 1, 1, 0, 1, 0, 0, 1]
    y_pred = [0, 1, 0, 0, 1, 0, 1, 1, 0, 1]
    
    metrics = ClassificationMetrics(y_true, y_pred, labels=['Negative', 'Positive'])
    print(f"Accuracy: {metrics.accuracy():.4f}")
    print(f"Precision: {metrics.precision():.4f}")
    print(f"Recall: {metrics.recall():.4f}")
    print(f"F1 Score: {metrics.f1():.4f}")
    print("\nClassification Report:")
    print(metrics.classification_report())
    
    # Test generation metrics
    print("\n" + "="*60)
    print("Generation Metrics:")
    ref_text = "the cat sat on the mat"
    hyp_text = "the cat is on the mat"
    
    bleu = GenerationMetrics.calculate_bleu(ref_text, hyp_text)
    rouge = GenerationMetrics.calculate_rouge(ref_text, hyp_text)
    
    print(f"BLEU Score: {bleu:.4f}")
    print(f"ROUGE F1 Score: {rouge:.4f}")
    
    # Test NER metrics
    print("\n" + "="*60)
    print("NER Metrics:")
    true_entities = ['Apple', 'Google', 'Microsoft']
    pred_entities = ['Apple', 'Google', 'Amazon']
    
    ner_metrics = NERMetrics.calculate_entity_metrics(true_entities, pred_entities)
    print(f"Precision: {ner_metrics['precision']:.4f}")
    print(f"Recall: {ner_metrics['recall']:.4f}")
    print(f"F1 Score: {ner_metrics['f1']:.4f}")
    
    # Test model comparison
    print("\n" + "="*60)
    print("Model Comparison:")
    comparison = ModelComparison()
    comparison.add_result('Model A', {'accuracy': 0.92, 'f1': 0.89})
    comparison.add_result('Model B', {'accuracy': 0.95, 'f1': 0.93})
    comparison.add_result('Model C', {'accuracy': 0.90, 'f1': 0.87})
    
    results = comparison.compare()
    print("Comparison Results:")
    for metric, models in results.items():
        print(f"\n{metric}:")
        for model, score in models.items():
            if score is not None:
                print(f"  {model}: {score:.4f}")
