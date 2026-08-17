"""FastAPI backend for NLP Transformer System."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
import torch
import asyncio
from functools import lru_cache
import time

# Import NLP modules
from src.sentiment import SentimentPipeline
from src.ner import NERPipeline
from src.text_generation import TextGenerator
from src.summarization import SummarizerPipeline
from src.translation import TranslationPipeline


# FastAPI app initialization
app = FastAPI(
    title="NLP Transformer System API",
    description="API for transformer-based NLP tasks",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Request/Response Models ====================

class TextRequest(BaseModel):
    """Basic text input request."""
    text: str = Field(..., min_length=1, max_length=10000, description="Input text")


class SentimentRequest(BaseModel):
    """Sentiment analysis request."""
    text: str = Field(..., min_length=1, max_length=1000, description="Text to analyze")
    return_probabilities: bool = Field(False, description="Return probability scores")


class SentimentResponse(BaseModel):
    """Sentiment analysis response."""
    text: str
    sentiment: str
    confidence: float
    probabilities: Optional[dict] = None


class NERRequest(BaseModel):
    """NER request."""
    text: str = Field(..., min_length=1, max_length=5000, description="Text for NER")


class Entity(BaseModel):
    """Entity model."""
    text: str
    type: str
    confidence: Optional[float] = None


class NERResponse(BaseModel):
    """NER response."""
    text: str
    entities: List[Entity]


class GenerationRequest(BaseModel):
    """Text generation request."""
    prompt: str = Field(..., min_length=1, description="Starting prompt")
    max_length: int = Field(100, ge=10, le=500, description="Max tokens")
    method: str = Field("nucleus", description="Generation method")
    temperature: float = Field(0.7, ge=0.1, le=2.0, description="Temperature")
    top_k: Optional[int] = Field(50, ge=1, le=100, description="Top-K value")
    top_p: Optional[float] = Field(0.9, ge=0.0, le=1.0, description="Top-P value")


class GenerationResponse(BaseModel):
    """Text generation response."""
    prompt: str
    generated_text: str
    method: str
    processing_time: float


class SummarizationRequest(BaseModel):
    """Summarization request."""
    text: str = Field(..., min_length=10, max_length=50000, description="Text to summarize")
    min_length: int = Field(50, ge=10, le=500, description="Min summary length")
    max_length: int = Field(150, ge=50, le=1000, description="Max summary length")


class SummarizationResponse(BaseModel):
    """Summarization response."""
    original_text: str
    summary: str
    compression_ratio: float
    processing_time: float


class TranslationRequest(BaseModel):
    """Translation request."""
    text: str = Field(..., min_length=1, max_length=10000, description="Text to translate")
    source_language: str = Field("en", description="Source language code")
    target_language: str = Field("fr", description="Target language code")


class TranslationResponse(BaseModel):
    """Translation response."""
    text: str
    translation: str
    source_language: str
    target_language: str
    processing_time: float


class BatchRequest(BaseModel):
    """Batch processing request."""
    texts: List[str] = Field(..., min_items=1, max_items=100, description="Batch of texts")
    task: str = Field(..., description="Task type: sentiment, ner, etc.")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    device: str
    models_loaded: List[str]


# ==================== Model Caching ====================

_models = {}


def get_sentiment_model():
    """Get cached sentiment model."""
    if 'sentiment' not in _models:
        _models['sentiment'] = SentimentPipeline()
    return _models['sentiment']


def get_ner_model():
    """Get cached NER model."""
    if 'ner' not in _models:
        _models['ner'] = NERPipeline()
    return _models['ner']


def get_generation_model():
    """Get cached generation model."""
    if 'generation' not in _models:
        _models['generation'] = TextGenerator("gpt2")
    return _models['generation']


def get_summarization_model():
    """Get cached summarization model."""
    if 'summarization' not in _models:
        _models['summarization'] = SummarizerPipeline()
    return _models['summarization']


def get_translation_model(source, target):
    """Get cached translation model."""
    key = f"translation_{source}_{target}"
    if key not in _models:
        _models[key] = TranslationPipeline(source, target)
    return _models[key]


# ==================== Endpoints ====================

@app.get("/", response_model=dict)
async def root():
    """Root endpoint."""
    return {
        "message": "NLP Transformer System API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        device="CUDA (GPU)" if torch.cuda.is_available() else "CPU",
        models_loaded=list(_models.keys())
    )


# ==================== Sentiment Analysis ====================

@app.post("/sentiment", response_model=SentimentResponse)
async def analyze_sentiment(request: SentimentRequest):
    """
    Analyze sentiment of input text.
    
    - **text**: Input text to analyze
    - **return_probabilities**: Whether to return probability scores
    """
    try:
        start_time = time.time()
        model = get_sentiment_model()
        
        result = model.predict(request.text)
        
        return SentimentResponse(
            text=result['text'],
            sentiment=result['sentiment'],
            confidence=result['confidence'],
            probabilities=result.get('probabilities') if request.return_probabilities else None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing sentiment: {str(e)}")


@app.post("/sentiment/batch")
async def analyze_sentiment_batch(request: BatchRequest):
    """Batch sentiment analysis."""
    if request.task != "sentiment":
        raise HTTPException(status_code=400, detail="Task must be 'sentiment'")
    
    try:
        model = get_sentiment_model()
        results = model.predict_batch(request.texts)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in batch analysis: {str(e)}")


# ==================== Named Entity Recognition ====================

@app.post("/ner", response_model=NERResponse)
async def extract_entities(request: NERRequest):
    """
    Extract named entities from text.
    
    - **text**: Input text for NER
    """
    try:
        model = get_ner_model()
        result = model.predict(request.text)
        
        entities = [
            Entity(
                text=e['text'],
                type=e['type'],
                confidence=e.get('confidence')
            )
            for e in result['entities']
        ]
        
        return NERResponse(
            text=result['text'],
            entities=entities
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting entities: {str(e)}")


@app.post("/ner/batch")
async def extract_entities_batch(request: BatchRequest):
    """Batch NER processing."""
    if request.task != "ner":
        raise HTTPException(status_code=400, detail="Task must be 'ner'")
    
    try:
        model = get_ner_model()
        results = model.predict_batch(request.texts)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in batch NER: {str(e)}")


# ==================== Text Generation ====================

@app.post("/generate", response_model=GenerationResponse)
async def generate_text(request: GenerationRequest):
    """
    Generate text using specified method.
    
    - **prompt**: Starting prompt
    - **max_length**: Maximum tokens to generate
    - **method**: "greedy", "topk", "nucleus", or "beam_search"
    - **temperature**: Controls randomness (0.1-2.0)
    """
    try:
        start_time = time.time()
        model = get_generation_model()
        
        # Prepare kwargs based on method
        kwargs = {
            'max_length': request.max_length,
            'temperature': request.temperature
        }
        
        if request.method == "topk":
            kwargs['k'] = request.top_k or 50
        elif request.method == "nucleus":
            kwargs['p'] = request.top_p or 0.9
        
        result = model.generate(request.prompt, method=request.method, **kwargs)
        processing_time = time.time() - start_time
        
        return GenerationResponse(
            prompt=request.prompt,
            generated_text=result,
            method=request.method,
            processing_time=processing_time
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating text: {str(e)}")


# ==================== Summarization ====================

@app.post("/summarize", response_model=SummarizationResponse)
async def summarize_text(request: SummarizationRequest):
    """
    Summarize input text.
    
    - **text**: Text to summarize
    - **min_length**: Minimum summary length
    - **max_length**: Maximum summary length
    """
    try:
        start_time = time.time()
        model = get_summarization_model()
        
        summary = model.summarize(
            request.text,
            min_length=request.min_length,
            max_length=request.max_length
        )
        processing_time = time.time() - start_time
        
        compression_ratio = len(summary.split()) / len(request.text.split())
        
        return SummarizationResponse(
            original_text=request.text,
            summary=summary,
            compression_ratio=compression_ratio,
            processing_time=processing_time
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error summarizing text: {str(e)}")


# ==================== Translation ====================

@app.post("/translate", response_model=TranslationResponse)
async def translate_text(request: TranslationRequest):
    """
    Translate text to target language.
    
    - **text**: Text to translate
    - **source_language**: Source language code
    - **target_language**: Target language code
    """
    try:
        start_time = time.time()
        model = get_translation_model(request.source_language, request.target_language)
        
        if model.pipeline is None:
            raise HTTPException(
                status_code=400,
                detail=f"Translation model not available for {request.source_language}-{request.target_language}"
            )
        
        translation = model.translate(request.text)
        processing_time = time.time() - start_time
        
        return TranslationResponse(
            text=request.text,
            translation=translation,
            source_language=request.source_language,
            target_language=request.target_language,
            processing_time=processing_time
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error translating text: {str(e)}")


# ==================== Batch Processing ====================

@app.post("/batch")
async def batch_process(request: BatchRequest):
    """
    Batch process multiple texts for the specified task.
    
    - **texts**: List of texts to process
    - **task**: Task type (sentiment, ner, etc.)
    """
    try:
        if request.task == "sentiment":
            model = get_sentiment_model()
            results = model.predict_batch(request.texts)
        elif request.task == "ner":
            model = get_ner_model()
            results = model.predict_batch(request.texts)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown task: {request.task}")
        
        return {
            "task": request.task,
            "count": len(request.texts),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in batch processing: {str(e)}")


# ==================== Exception Handling ====================

@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle ValueError exceptions."""
    return HTTPException(status_code=400, detail=str(exc))


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    return HTTPException(status_code=500, detail=f"Internal server error: {str(exc)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
