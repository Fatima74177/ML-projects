"""Machine translation using pre-trained models."""
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM


class Translator:
    """Machine translation using MarianMT and T5 models."""
    
    def __init__(self, source_lang="en", target_lang="fr"):
        """
        Initialize translator.
        
        Args:
            source_lang: Source language code (e.g., 'en')
            target_lang: Target language code (e.g., 'fr')
        """
        self.source_lang = source_lang
        self.target_lang = target_lang
        
        # Model name follows format: Helsinki-NLP/opus-mt-{src}-{tgt}
        self.model_name = f"Helsinki-NLP/opus-mt-{source_lang}-{target_lang}"
        
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.model.eval()
    
    def translate(self, text, max_length=500):
        """
        Translate text from source to target language.
        
        Args:
            text: Text to translate
            max_length: Maximum length of translation
        
        Returns:
            Translated text
        """
        # Tokenize
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Generate translation
        with torch.no_grad():
            translated_ids = self.model.generate(
                inputs['input_ids'],
                attention_mask=inputs['attention_mask'],
                max_length=max_length,
                num_beams=4,
                early_stopping=True,
            )
        
        # Decode
        translation = self.tokenizer.decode(translated_ids[0], skip_special_tokens=True)
        return translation
    
    def translate_batch(self, texts, max_length=500):
        """
        Translate multiple texts.
        
        Args:
            texts: List of texts to translate
            max_length: Maximum length of translation
        
        Returns:
            List of translated texts
        """
        translations = []
        for text in texts:
            translation = self.translate(text, max_length)
            translations.append(translation)
        return translations


class TranslationPipeline:
    """Translation wrapper compatible with Transformers 4 and 5.

    Helsinki models directly cover English pairs. Other supported pairs are
    translated through English, which avoids relying on unavailable pair-specific
    models such as ``opus-mt-fr-de``.
    """
    
    def __init__(self, source_lang="en", target_lang="fr"):
        """Initialize translation pipeline."""
        self.source_lang = source_lang
        self.target_lang = target_lang
        supported = {"en", "fr", "de", "es"}
        if source_lang not in supported or target_lang not in supported:
            raise ValueError(f"Unsupported language pair: {source_lang}-{target_lang}")

        if source_lang == target_lang:
            self.translators = []
        elif "en" in (source_lang, target_lang):
            self.translators = [Translator(source_lang, target_lang)]
        else:
            self.translators = [
                Translator(source_lang, "en"),
                Translator("en", target_lang),
            ]
    
    def translate(self, text):
        """Translate text using pipeline."""
        translation = text
        for translator in self.translators:
            translation = translator.translate(translation)
        return translation
    
    def translate_batch(self, texts):
        """Translate multiple texts."""
        return [self.translate(text) for text in texts]


# Supported language pairs
SUPPORTED_LANGUAGES = ("en", "fr", "de", "es")
SUPPORTED_LANGUAGE_PAIRS = [
    (source, target)
    for source in SUPPORTED_LANGUAGES
    for target in SUPPORTED_LANGUAGES
    if source != target
]


def get_available_translators():
    """Get list of available language pair translators."""
    return SUPPORTED_LANGUAGE_PAIRS


# Example usage and testing
if __name__ == "__main__":
    print("Testing Machine Translation:")
    print("="*60)
    
    texts = [
        "Hello, how are you?",
        "The weather is beautiful today.",
        "I love learning new languages.",
    ]
    
    # English to French
    print("English to French Translation:")
    print("-" * 60)
    try:
        translator_fr = TranslationPipeline("en", "fr")
        for text in texts:
            try:
                translation = translator_fr.translate(text)
                print(f"EN: {text}")
                print(f"FR: {translation}")
                print()
            except Exception as e:
                print(f"Error translating '{text}': {e}")
    except Exception as e:
        print(f"Error initializing translator: {e}")
        print("Note: Translation models need to be downloaded from Hugging Face Hub")
    
    # English to German
    print("\n" + "="*60)
    print("English to German Translation:")
    print("-" * 60)
    try:
        translator_de = TranslationPipeline("en", "de")
        for text in texts:
            try:
                translation = translator_de.translate(text)
                print(f"EN: {text}")
                print(f"DE: {translation}")
                print()
            except Exception as e:
                print(f"Error translating '{text}': {e}")
    except Exception as e:
        print(f"Error initializing translator: {e}")
