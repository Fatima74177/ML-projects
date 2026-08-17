"""Text preprocessing utilities."""
import re
import string
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')


class TextPreprocessor:
    """Preprocess text data for NLP tasks."""
    
    def __init__(self, lowercase=True, remove_punctuation=True, remove_numbers=False, 
                 remove_stopwords=False, stem=False):
        self.lowercase = lowercase
        self.remove_punctuation = remove_punctuation
        self.remove_numbers = remove_numbers
        self.remove_stopwords = remove_stopwords
        self.stem = stem
        self.stemmer = PorterStemmer()
        self.stop_words = set(stopwords.words('english'))
    
    def clean_text(self, text):
        """Remove HTML tags, URLs, and extra whitespace."""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Remove URLs
        text = re.sub(r'http\S+|www.\S+', '', text)
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def preprocess(self, text):
        """Apply full preprocessing pipeline."""
        # Clean text
        text = self.clean_text(text)
        
        # Lowercase
        if self.lowercase:
            text = text.lower()
        
        # Remove numbers
        if self.remove_numbers:
            text = re.sub(r'\d+', '', text)
        
        # Remove punctuation
        if self.remove_punctuation:
            text = text.translate(str.maketrans('', '', string.punctuation))
        
        # Tokenize
        tokens = word_tokenize(text)
        
        # Remove stopwords
        if self.remove_stopwords:
            tokens = [token for token in tokens if token not in self.stop_words]
        
        # Stem
        if self.stem:
            tokens = [self.stemmer.stem(token) for token in tokens]
        
        return ' '.join(tokens)
    
    def batch_preprocess(self, texts):
        """Preprocess multiple texts."""
        return [self.preprocess(text) for text in texts]


def create_preprocessor(config=None):
    """Factory function to create a preprocessor with configuration."""
    if config is None:
        config = {}
    return TextPreprocessor(**config)
