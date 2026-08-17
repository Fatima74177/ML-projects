"""Streamlit NLP Transformer System Application."""
import streamlit as st
import importlib

# Use Streamlit's resource cache for heavy model objects to survive reruns
try:
    cache_resource = st.cache_resource
except Exception:
    # Fallback for older Streamlit versions
    def cache_resource(func=None, **_):
        if func is None:
            def _decorator(f):
                return f
            return _decorator
        return func


# Page configuration
st.set_page_config(
    page_title="🧠 NLP Transformer System",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .task-header {
        font-size: 2rem;
        font-weight: bold;
        color: #2ca02c;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .result-box {
        background-color: #f0f0f0;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state for caching models
if 'sentiment_model' not in st.session_state:
    st.session_state.sentiment_model = None
if 'ner_model' not in st.session_state:
    st.session_state.ner_model = None
if 'gen_model' not in st.session_state:
    st.session_state.gen_model = None
if 'summary_model' not in st.session_state:
    st.session_state.summary_model = None


def load_sentiment_model():
    """Load sentiment analysis model."""
    if st.session_state.sentiment_model is None:
        with st.spinner("Loading sentiment model..."):
            st.session_state.sentiment_model = _cached_sentiment_pipeline()
    return st.session_state.sentiment_model


def load_ner_model():
    """Load NER model."""
    if st.session_state.ner_model is None:
        with st.spinner("Loading NER model..."):
            st.session_state.ner_model = _cached_ner_pipeline()
    return st.session_state.ner_model


def load_gen_model():
    """Load text generation model."""
    if st.session_state.gen_model is None:
        with st.spinner("Loading text generation model..."):
            st.session_state.gen_model = _cached_gen_pipeline()
    return st.session_state.gen_model


def load_summary_model():
    """Load summarization model."""
    if st.session_state.summary_model is None:
        with st.spinner("Loading summarization model..."):
            st.session_state.summary_model = _cached_summary_pipeline()
    return st.session_state.summary_model


# Cached constructors for heavy resources
@cache_resource
def _cached_sentiment_pipeline():
    mod = importlib.import_module('src.sentiment')
    SentimentPipeline = getattr(mod, 'SentimentPipeline')
    return SentimentPipeline()


@cache_resource
def _cached_ner_pipeline():
    mod = importlib.import_module('src.ner')
    NERPipeline = getattr(mod, 'NERPipeline')
    return NERPipeline()


@cache_resource
def _cached_gen_pipeline():
    mod = importlib.import_module('src.text_generation')
    TextGenerator = getattr(mod, 'TextGenerator')
    return TextGenerator("distilgpt2")


@cache_resource
def _cached_summary_pipeline():
    mod = importlib.import_module('src.summarization')
    SummarizerPipeline = getattr(mod, 'SummarizerPipeline')
    return SummarizerPipeline()


@cache_resource
def _cached_translation_pipeline(source_lang, target_lang):
    mod = importlib.import_module('src.translation')
    TranslationPipeline = getattr(mod, 'TranslationPipeline')
    return TranslationPipeline(source_lang, target_lang)


def home_page():
    """Home page."""
    st.markdown("<div class='main-header'>🧠 NLP Transformer System</div>", unsafe_allow_html=True)
    
    st.markdown("""
    ### Welcome to the NLP Transformer Studio!
    
    A comprehensive **Transformer-based NLP toolkit** for modern text processing and understanding.
    
    **Key Features:**
    - 😊 **Sentiment Analysis**: Classify text emotions using DistilBERT
    - ✍️ **Text Generation**: Generate creative text with multiple sampling strategies
    - 🏷️ **Named Entity Recognition**: Extract entities (people, places, organizations)
    - 📄 **Summarization**: Compress long texts into concise summaries
    - 🌐 **Translation**: Translate between multiple languages
    - 📊 **Evaluation**: Comprehensive model evaluation and comparison
    - 🤖 **Transformer Architecture**: Educational implementations from scratch
    
    **Select a task from the sidebar to get started!**
    """)
    
    # Display available device if torch is installed
    try:
        torch = importlib.import_module('torch')
        device_str = 'CUDA (GPU)' if torch.cuda.is_available() else 'CPU'
    except Exception:
        device_str = 'torch not installed'

    st.sidebar.info(f"🖥️ **Device**: {device_str}")


def sentiment_analysis_page():
    """Sentiment analysis page."""
    st.markdown("<div class='task-header'>😊 Sentiment Analysis</div>", unsafe_allow_html=True)
    
    st.markdown("""
    Analyze the emotional sentiment of text using a fine-tuned DistilBERT model.
    This model is trained to classify text as positive or negative.
    """)
    
    # Load model
    model = load_sentiment_model()
    
    # Input options
    col1, col2 = st.columns([2, 1])
    with col1:
        text_input = st.text_area("Enter text to analyze:", height=150)
    
    with col2:
        st.markdown("### Options")
        show_probabilities = st.checkbox("Show confidence scores", value=True)
    
    if st.button("Analyze Sentiment", key="sentiment_analyze"):
        if text_input.strip():
            result = model.predict(text_input)
            
            # Display result
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown("<div class='result-box'>", unsafe_allow_html=True)
                
                # Display sentiment with emoji
                sentiment = result['sentiment']
                emoji = "😊" if sentiment == "POSITIVE" else "😞"
                confidence = result['confidence']
                
                st.markdown(f"### {emoji} {sentiment}")
                st.markdown(f"**Confidence**: {confidence:.1%}")
                
                # Progress bar
                st.progress(confidence)
                
                if show_probabilities:
                    st.markdown("#### Confidence Scores")
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.metric("Positive", f"{result['confidence']:.1%}")
                    with col_b:
                        st.metric("Negative", f"{1-result['confidence']:.1%}")
                
                st.markdown("</div>", unsafe_allow_html=True)
    
    # Batch analysis
    st.markdown("### Batch Analysis")
    batch_text = st.text_area("Enter multiple texts (one per line):", height=150)
    
    if st.button("Analyze Batch", key="sentiment_batch"):
        if batch_text.strip():
            texts = batch_text.strip().split('\n')
            results = model.predict_batch(texts)
            
            # Display results in table
            st.markdown("#### Results")
            for i, result in enumerate(results, 1):
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.text(result['text'][:50] + "..." if len(result['text']) > 50 else result['text'])
                with col2:
                    emoji = "😊" if result['sentiment'] == "POSITIVE" else "😞"
                    st.text(f"{emoji} {result['sentiment']}")
                with col3:
                    st.text(f"{result['confidence']:.1%}")


def ner_page():
    """Named Entity Recognition page."""
    st.markdown("<div class='task-header'>🏷️ Named Entity Recognition</div>", unsafe_allow_html=True)
    
    st.markdown("""
    Extract and identify named entities in text such as people, organizations, locations, and dates.
    """)
    
    # Load model
    model = load_ner_model()
    
    # Input
    text_input = st.text_area("Enter text to analyze:", height=150)
    
    if st.button("Extract Entities", key="ner_analyze"):
        if text_input.strip():
            try:
                result = model.predict(text_input)
                
                # Display result
                st.markdown("<div class='result-box'>", unsafe_allow_html=True)
                ner_mod = importlib.import_module('src.ner')
                format_ner_results = getattr(ner_mod, 'format_ner_results')
                st.markdown(format_ner_results(result))
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Display as table
                if result.get('entities'):
                    st.markdown("#### Entities Table")
                    entities_data = []
                    for entity in result['entities']:
                        entities_data.append({
                            'Entity': entity.get('text', 'N/A'),
                            'Type': entity.get('type', 'UNKNOWN'),
                            'Confidence': entity.get('confidence', 'N/A')
                        })
                    st.dataframe(entities_data)
            except Exception as e:
                st.error(f"❌ NER Error: {e}")


def text_generation_page():
    """Text generation page."""
    st.markdown("<div class='task-header'>✍️ Text Generation</div>", unsafe_allow_html=True)
    
    st.markdown("""
    Generate creative continuations of text using DistilGPT-2 with multiple sampling strategies.
    """)
    
    # Load model
    model = load_gen_model()
    
    # Input
    col1, col2 = st.columns([2, 1])
    with col1:
        prompt = st.text_input("Enter a prompt:", value="Once upon a time")
    with col2:
        max_length = st.slider("Max tokens:", 20, 150, 80)
    
    # Generation parameters
    col1, col2, col3 = st.columns(3)
    with col1:
        method = st.selectbox(
            "Sampling method:",
            ["greedy", "topk", "nucleus", "beam_search"]
        )
    with col2:
        temperature = st.slider("Temperature:", 0.1, 2.0, 0.7)
    with col3:
        if method == "topk":
            k = st.slider("Top-K:", 1, 100, 50)
        elif method == "nucleus":
            p = st.slider("Top-P:", 0.0, 1.0, 0.9)
    
    if st.button("Generate", key="generation_generate"):
        if prompt.strip():
            try:
                if method == "greedy":
                    result = model.generate(prompt, method=method, max_length=max_length, temperature=temperature)
                elif method == "topk":
                    result = model.generate(prompt, method=method, max_length=max_length, k=k, temperature=temperature)
                elif method == "nucleus":
                    result = model.generate(prompt, method=method, max_length=max_length, p=p, temperature=temperature)
                else:
                    result = model.generate(prompt, method=method, max_length=max_length)

                # Check if running in demo mode
                if "[Note: Running in demo mode" in str(result):
                    st.info("📌 **Demo Mode**: GPT-2 model is unavailable. Showing demo output.")
                    st.markdown("<div class='result-box'>", unsafe_allow_html=True)
                    st.markdown(f"**Generated Text (Demo):**\n\n{result}")
                    st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='result-box'>", unsafe_allow_html=True)
                    st.markdown(f"**Generated Text:**\n\n{result}")
                    st.markdown("</div>", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"❌ Error generating text: {e}")


def summarization_page():
    """Text summarization page."""
    st.markdown("<div class='task-header'>📄 Text Summarization</div>", unsafe_allow_html=True)
    
    st.markdown("""
    Compress long texts into concise summaries using a cloud-friendly T5 model.
    """)
    
    # Load model
    model = load_summary_model()
    
    # Input
    text_input = st.text_area("Enter text to summarize:", height=250)
    
    # Parameters
    col1, col2 = st.columns(2)
    with col1:
        min_length = st.slider("Min summary length:", 20, 200, 50)
    with col2:
        max_length = st.slider("Max summary length:", 50, 500, 150)
    
    if st.button("Summarize", key="summarization_summarize"):
        if text_input.strip():
            try:
                with st.spinner("Generating summary..."):
                    summary = model.summarize(text_input, min_length=min_length, max_length=max_length)
                
                st.markdown("<div class='result-box'>", unsafe_allow_html=True)
                st.markdown("#### Summary")
                st.markdown(summary)
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Display statistics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Original length", len(text_input.split()))
                with col2:
                    st.metric("Summary length", len(summary.split()))
                with col3:
                    ratio = len(summary.split()) / len(text_input.split()) if text_input else 0
                    st.metric("Compression ratio", f"{ratio:.1%}")
            except Exception as e:
                st.error(f"Error summarizing text: {e}")


def translation_page():
    """Machine translation page."""
    st.markdown("<div class='task-header'>🌐 Machine Translation</div>", unsafe_allow_html=True)
    
    st.markdown("""
    Translate text between multiple languages using transformer models.
    """)
    
    languages = {
        "en": "English",
        "fr": "French",
        "de": "German",
        "es": "Spanish",
    }

    # Language selection
    col1, col2 = st.columns(2)
    with col1:
        source_lang = st.selectbox(
            "Source language:",
            list(languages),
            format_func=lambda code: languages[code],
        )
    with col2:
        target_lang = st.selectbox(
            "Target language:",
            list(languages),
            index=1,
            format_func=lambda code: languages[code],
        )
    
    # Text input
    text_input = st.text_area("Enter text to translate:", height=150)
    
    if st.button("Translate", key="translation_translate"):
        if text_input.strip():
            try:
                with st.spinner("Translating..."):
                    translator = _cached_translation_pipeline(source_lang, target_lang)
                    translation = translator.translate(text_input)
                
                if translation:
                    st.markdown("<div class='result-box'>", unsafe_allow_html=True)
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**{languages[source_lang]}**")
                        st.text(text_input)
                    with col2:
                        st.markdown(f"**{languages[target_lang]}**")
                        st.text(translation)
                    st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.error("Translation failed. Model not available for this language pair.")
            except Exception as e:
                st.error(f"Error translating text: {e}")


def evaluation_page():
    """Model evaluation and comparison page."""
    st.markdown("<div class='task-header'>📊 Model Evaluation</div>", unsafe_allow_html=True)
    
    st.markdown("""
    Evaluate and compare model performance using various metrics.
    """)
    
    # Evaluation type selection
    eval_type = st.radio("Select evaluation type:", ["Classification", "Generation", "Model Comparison"])
    
    if eval_type == "Classification":
        st.markdown("#### Classification Metrics")
        
        # Sample data for demonstration
        y_true = [0, 1, 0, 1, 1, 0, 1, 0, 0, 1, 1, 0]
        y_pred = [0, 1, 0, 0, 1, 0, 1, 1, 0, 1, 1, 0]
        
        eval_mod = importlib.import_module('src.evaluation')
        ClassificationMetrics = getattr(eval_mod, 'ClassificationMetrics')
        metrics = ClassificationMetrics(y_true, y_pred, labels=['Negative', 'Positive'])
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Accuracy", f"{metrics.accuracy():.3f}")
        with col2:
            st.metric("Precision", f"{metrics.precision():.3f}")
        with col3:
            st.metric("Recall", f"{metrics.recall():.3f}")
        with col4:
            st.metric("F1 Score", f"{metrics.f1():.3f}")
        
        st.markdown("#### Classification Report")
        st.text(metrics.classification_report())
    
    elif eval_type == "Generation":
        st.markdown("#### Generation Metrics")
        
        ref_text = st.text_input("Reference text:", "the cat sat on the mat")
        hyp_text = st.text_input("Generated text:", "the cat is on the mat")
        
        if st.button("Calculate Metrics"):
            eval_mod = importlib.import_module('src.evaluation')
            GenerationMetrics = getattr(eval_mod, 'GenerationMetrics')
            bleu = GenerationMetrics.calculate_bleu(ref_text, hyp_text)
            rouge = GenerationMetrics.calculate_rouge(ref_text, hyp_text)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("BLEU Score", f"{bleu:.3f}")
            with col2:
                st.metric("ROUGE F1 Score", f"{rouge:.3f}")
    
    else:
        st.markdown("#### Model Comparison")
        
        eval_mod = importlib.import_module('src.evaluation')
        ModelComparison = getattr(eval_mod, 'ModelComparison')
        comparison = ModelComparison()
        comparison.add_result('DistilBERT', {'accuracy': 0.92, 'f1': 0.89, 'inference_time': 0.05})
        comparison.add_result('BERT', {'accuracy': 0.95, 'f1': 0.93, 'inference_time': 0.12})
        comparison.add_result('RoBERTa', {'accuracy': 0.94, 'f1': 0.91, 'inference_time': 0.15})
        
        results = comparison.compare()
        
        # Display comparison as table
        st.markdown("#### Performance Comparison")
        
        # Create comparison dataframe
        comparison_data = {}
        for metric in results:
            comparison_data[metric] = results[metric]
        
        st.dataframe(comparison_data)


def about_page():
    """About page."""
    st.markdown("<div class='main-header'>ℹ️ About This Project</div>", unsafe_allow_html=True)
    
    st.markdown("""
    ### 🧠 NLP Transformer System
    
    A comprehensive Natural Language Processing toolkit built with state-of-the-art transformer models.
    
    **Technologies:**
    - PyTorch: Deep learning framework
    - Hugging Face Transformers: Pre-trained models
    - DistilBERT: Efficient sentiment classification
    - GPT-2: Text generation
    - BART: Text summarization
    - Helsinki-NLP: Machine translation
    - Streamlit: Web interface
    - FastAPI: REST API backend
    
    **Features:**
    - Sentiment Analysis with confidence scores
    - Named Entity Recognition (NER)
    - Text Generation with multiple sampling strategies
    - Automatic Text Summarization
    - Multi-language Translation
    - Model Evaluation and Comparison
    - Educational Transformer Implementation
    
    **Model Information:**
    - Sentiment: `distilbert-base-uncased-finetuned-sst-2-english`
    - NER: `dslim/distilbert-NER`
    - Generation: `distilgpt2`
    - Summarization: `google-t5/t5-small`
    - Translation: `Helsinki-NLP/opus-mt`
    
    **Performance Targets:**
    - Sentiment Classification: >90% accuracy
    - Generation: <1 second per 100 tokens
    - Inference: GPU-accelerated for speed
    
    **Author**: NLP Research Team
    **License**: MIT
    """)


# Main app logic
def main():
    """Main application."""
    # Sidebar
    st.sidebar.title("🧠 NLP Transformer System")
    
    pages = {
        "🏠 Home": home_page,
        "😊 Sentiment Analysis": sentiment_analysis_page,
        "🏷️ Named Entity Recognition": ner_page,
        "✍️ Text Generation": text_generation_page,
        "📄 Summarization": summarization_page,
        "🌐 Translation": translation_page,
        "📊 Evaluation": evaluation_page,
        "ℹ️ About": about_page,
    }
    
    selected_page = st.sidebar.radio("Select a task:", list(pages.keys()))
    
    # Run selected page
    pages[selected_page]()


if __name__ == "__main__":
    main()
