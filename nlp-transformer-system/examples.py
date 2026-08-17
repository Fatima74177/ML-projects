"""Example usage and testing script for NLP Transformer System."""
import sys
import torch

print("=" * 70)
print("🧠 NLP Transformer System - Feature Demonstration")
print("=" * 70)
print(f"\n📱 Environment Info:")
print(f"  Python: {sys.version.split()[0]}")
print(f"  PyTorch: {torch.__version__}")
print(f"  Device: {'CUDA (GPU)' if torch.cuda.is_available() else 'CPU'}")

# ==================== 1. Sentiment Analysis ====================
print("\n" + "=" * 70)
print("1️⃣ SENTIMENT ANALYSIS")
print("=" * 70)

try:
    from src.sentiment import SentimentPipeline
    
    analyzer = SentimentPipeline()
    texts = [
        "I absolutely love this product! It's amazing!",
        "This is terrible. Very disappointed.",
        "It's okay, nothing special.",
    ]
    
    print("\n📊 Analyzing sentiments...")
    for text in texts:
        result = analyzer.predict(text)
        emoji = "😊" if result['sentiment'] == "POSITIVE" else "😞"
        print(f"\n  Text: {text[:50]}...")
        print(f"  {emoji} Sentiment: {result['sentiment']}")
        print(f"  Confidence: {result['confidence']:.1%}")
except Exception as e:
    print(f"❌ Error: {e}")

# ==================== 2. Named Entity Recognition ====================
print("\n" + "=" * 70)
print("2️⃣ NAMED ENTITY RECOGNITION (NER)")
print("=" * 70)

try:
    from src.ner import NERPipeline
    
    ner = NERPipeline()
    texts = [
        "Elon Musk founded Tesla in California.",
        "Apple Inc. is led by Tim Cook.",
        "The meeting is scheduled for January 15th at Google headquarters.",
    ]
    
    print("\n🏷️ Extracting entities...")
    for text in texts:
        result = ner.predict(text)
        print(f"\n  Text: {text}")
        print("  Entities:")
        for entity in result['entities']:
            print(f"    - {entity['text']}: {entity['type']} ({entity.get('confidence', 'N/A')})")
except Exception as e:
    print(f"❌ Error: {e}")

# ==================== 3. Preprocessing & Tokenization ====================
print("\n" + "=" * 70)
print("3️⃣ TEXT PREPROCESSING & TOKENIZATION")
print("=" * 70)

try:
    from src.preprocessing import TextPreprocessor
    from src.tokenizer import create_tokenizer
    
    # Preprocessing
    print("\n🧹 Text preprocessing...")
    preprocessor = TextPreprocessor(lowercase=True, remove_punctuation=True)
    raw_text = "Hello! This is a SAMPLE text, with punctuation and numbers 123."
    cleaned = preprocessor.preprocess(raw_text)
    print(f"  Original: {raw_text}")
    print(f"  Cleaned:  {cleaned}")
    
    # Tokenization
    print("\n🔤 Tokenization...")
    tokenizer = create_tokenizer("pretrained", "bert-base-uncased")
    text = "Hello, this is a test sentence for tokenization."
    encoding = tokenizer.encode(text)
    print(f"  Text: {text}")
    print(f"  Tokens: {encoding['input_ids'][:10]}...")  # Show first 10
    print(f"  Vocab size: {tokenizer.get_vocab_size()}")
except Exception as e:
    print(f"❌ Error: {e}")

# ==================== 4. Custom Transformer ====================
print("\n" + "=" * 70)
print("4️⃣ TRANSFORMER ARCHITECTURE (FROM SCRATCH)")
print("=" * 70)

try:
    from src.transformer import Transformer, TransformerEncoderOnly
    
    print("\n🤖 Testing transformer components...")
    
    # Encoder-only for classification
    vocab_size = 10000
    d_model = 256
    num_heads = 4
    
    model = TransformerEncoderOnly(
        vocab_size=vocab_size,
        d_model=d_model,
        num_heads=num_heads,
        num_layers=2,
        num_classes=2
    )
    
    # Test input
    batch_size = 2
    seq_len = 10
    input_ids = torch.randint(0, vocab_size, (batch_size, seq_len))
    
    with torch.no_grad():
        logits = model(input_ids)
    
    print(f"  Model: TransformerEncoderOnly")
    print(f"  Input shape: {input_ids.shape}")
    print(f"  Output shape: {logits.shape}")
    print(f"  Parameters: {sum(p.numel() for p in model.parameters()):,}")
    print(f"  ✅ Transformer working correctly!")
except Exception as e:
    print(f"❌ Error: {e}")

# ==================== 5. Text Generation ====================
print("\n" + "=" * 70)
print("5️⃣ TEXT GENERATION")
print("=" * 70)

try:
    from src.text_generation import TextGenerator
    
    print("\n✍️ Generating text with different methods...")
    generator = TextGenerator("gpt2")
    prompt = "The future of artificial intelligence"
    
    print(f"\n  Prompt: '{prompt}'")
    
    # Try greedy generation
    try:
        result = generator.generate(prompt, method="greedy", max_length=50, temperature=0.7)
        print(f"\n  🎯 Greedy:")
        print(f"     {result[:80]}...")
    except:
        print("  ⚠️ Greedy generation not available")
    
    # Try nucleus sampling
    try:
        result = generator.generate(prompt, method="nucleus", max_length=50, p=0.9, temperature=0.7)
        print(f"\n  🎲 Nucleus (Top-P):")
        print(f"     {result[:80]}...")
    except:
        print("  ⚠️ Nucleus sampling not available")
        
except Exception as e:
    print(f"❌ Error: {e}")

# ==================== 6. Text Summarization ====================
print("\n" + "=" * 70)
print("6️⃣ TEXT SUMMARIZATION")
print("=" * 70)

try:
    from src.summarization import SummarizerPipeline
    
    text = """
    Artificial intelligence is transforming many industries and aspects of human life.
    Machine learning models can now process vast amounts of data and identify patterns.
    Deep learning with neural networks has achieved remarkable success in many domains.
    However, AI also brings challenges including bias, privacy concerns, and job displacement.
    Responsible development and deployment of AI systems is crucial for the future.
    """
    
    summarizer = SummarizerPipeline()
    print("\n📄 Summarizing text...")
    print(f"  Original length: {len(text.split())} words")
    
    try:
        summary = summarizer.summarize(text, min_length=30, max_length=80)
        print(f"  Summary length: {len(summary.split())} words")
        print(f"  Summary: {summary}")
    except:
        print("  ⚠️ Summarization model not available")
except Exception as e:
    print(f"❌ Error: {e}")

# ==================== 7. Machine Translation ====================
print("\n" + "=" * 70)
print("7️⃣ MACHINE TRANSLATION")
print("=" * 70)

try:
    from src.translation import TranslationPipeline
    
    text = "Hello, how are you today?"
    
    print("\n🌐 Translating text...")
    print(f"  English: {text}")
    
    try:
        translator = TranslationPipeline("en", "fr")
        if translator.pipeline:
            translation = translator.translate(text)
            print(f"  French: {translation}")
        else:
            print("  ⚠️ Translation model not available")
    except:
        print("  ⚠️ Translation model not available")
except Exception as e:
    print(f"❌ Error: {e}")

# ==================== 8. Data Preparation ====================
print("\n" + "=" * 70)
print("8️⃣ DATA PREPARATION")
print("=" * 70)

try:
    from src.data_preparation import load_sst2_dataset, inspect_dataset
    
    print("\n📊 Loading SST-2 dataset...")
    dataset = load_sst2_dataset()
    
    print(f"  Dataset splits: {list(dataset.keys())}")
    for split in dataset:
        print(f"  {split.capitalize()}: {len(dataset[split])} examples")
    
    if len(dataset['train']) > 0:
        sample = dataset['train'][0]
        print(f"\n  Sample:")
        for key, value in sample.items():
            if isinstance(value, str):
                print(f"    {key}: {value[:60]}...")
            else:
                print(f"    {key}: {value}")
except Exception as e:
    print(f"❌ Error: {e}")

# ==================== 9. Evaluation Metrics ====================
print("\n" + "=" * 70)
print("9️⃣ EVALUATION METRICS")
print("=" * 70)

try:
    from src.evaluation import ClassificationMetrics, GenerationMetrics, ModelComparison
    
    print("\n📈 Classification metrics...")
    y_true = [0, 1, 0, 1, 1, 0, 1, 0, 0, 1]
    y_pred = [0, 1, 0, 0, 1, 0, 1, 1, 0, 1]
    
    metrics = ClassificationMetrics(y_true, y_pred, labels=['Negative', 'Positive'])
    print(f"  Accuracy: {metrics.accuracy():.3f}")
    print(f"  Precision: {metrics.precision():.3f}")
    print(f"  Recall: {metrics.recall():.3f}")
    print(f"  F1 Score: {metrics.f1():.3f}")
    
    print("\n📊 Generation metrics...")
    ref = "the cat sat on the mat"
    hyp = "the cat is on the mat"
    
    bleu = GenerationMetrics.calculate_bleu(ref, hyp)
    rouge = GenerationMetrics.calculate_rouge(ref, hyp)
    
    print(f"  Reference: {ref}")
    print(f"  Hypothesis: {hyp}")
    print(f"  BLEU Score: {bleu:.3f}")
    print(f"  ROUGE F1: {rouge:.3f}")
    
    print("\n🏆 Model comparison...")
    comparison = ModelComparison()
    comparison.add_result('Model A', {'accuracy': 0.92, 'f1': 0.89})
    comparison.add_result('Model B', {'accuracy': 0.95, 'f1': 0.93})
    
    results = comparison.compare()
    for metric, scores in results.items():
        print(f"  {metric}:")
        for model, score in scores.items():
            print(f"    {model}: {score:.3f}")
except Exception as e:
    print(f"❌ Error: {e}")

# ==================== Summary ====================
print("\n" + "=" * 70)
print("✅ FEATURE DEMONSTRATION COMPLETE")
print("=" * 70)

print("""
🚀 Next Steps:

1. Start the Streamlit web application:
   $ streamlit run app.py

2. Launch the FastAPI backend:
   $ uvicorn api.main:app --reload

3. Explore the interactive interface at:
   - Streamlit: http://localhost:8501
   - FastAPI Docs: http://localhost:8000/docs

4. Train custom models:
   $ python src/data_preparation.py

📚 Documentation:
   - See README.md for detailed setup and usage
   - Check individual src/*.py files for module documentation
   - View transformer/ folder for architecture details

💡 Tips:
   - Use GPU for faster inference: pip install torch-cuda
   - Reduce batch sizes if running out of memory
   - Pre-download models to avoid repeated downloads

Good luck! 🎉
""")
