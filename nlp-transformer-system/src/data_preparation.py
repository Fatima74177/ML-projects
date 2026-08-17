"""Data preparation and loading utilities."""
import os
import json
from datasets import load_dataset, Dataset
from sklearn.model_selection import train_test_split


PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PROJECT_ROOT, "..", "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")


def ensure_dirs():
    """Create necessary directories."""
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)


def load_imdb_dataset():
    """Load IMDb dataset from Hugging Face Datasets."""
    print("Loading IMDb dataset from Hugging Face Datasets...")
    dataset = load_dataset("imdb")
    return dataset


def load_sst2_dataset():
    """Load SST-2 dataset from Hugging Face Datasets."""
    print("Loading SST-2 dataset from Hugging Face Datasets...")
    dataset = load_dataset("glue", "sst2")
    return dataset


def load_ag_news_dataset():
    """Load AG News dataset."""
    print("Loading AG News dataset...")
    dataset = load_dataset("ag_news")
    return dataset


def load_wnut_ner_dataset():
    """Load WNUT NER dataset."""
    print("Loading WNUT NER dataset...")
    dataset = load_dataset("wnut_17")
    return dataset


def inspect_dataset(dataset, name="Dataset"):
    """Print dataset information."""
    print(f"\n{name} Information:")
    print(f"Splits: {dataset.column_names if hasattr(dataset, 'column_names') else list(dataset.keys())}")
    
    for split in dataset if isinstance(dataset, dict) else [dataset]:
        split_name = split if isinstance(dataset, dict) else 'train'
        split_data = dataset[split] if isinstance(dataset, dict) else dataset
        print(f"\n{split_name.upper()} Split:")
        print(f"  Total examples: {len(split_data)}")
        if len(split_data) > 0:
            print(f"  Example record:")
            print(f"    {split_data[0]}")


def create_custom_split(dataset, train_ratio=0.7, val_ratio=0.15, test_ratio=0.15, seed=42):
    """Create custom train/val/test splits."""
    assert train_ratio + val_ratio + test_ratio == 1.0, "Ratios must sum to 1.0"
    
    # Get train and temp (val + test)
    train_data, temp_data = train_test_split(
        dataset, test_size=(val_ratio + test_ratio), random_state=seed
    )
    
    # Split temp into val and test
    val_data, test_data = train_test_split(
        temp_data, test_size=test_ratio / (val_ratio + test_ratio), random_state=seed
    )
    
    return {
        'train': Dataset.from_dict(train_data),
        'validation': Dataset.from_dict(val_data),
        'test': Dataset.from_dict(test_data)
    }


def save_dataset(dataset, name, split_type="imdb"):
    """Save dataset to disk."""
    output_dir = os.path.join(PROCESSED_DIR, name)
    os.makedirs(output_dir, exist_ok=True)
    
    if isinstance(dataset, dict):
        for split, data in dataset.items():
            data.save_to_disk(os.path.join(output_dir, split))
    else:
        dataset.save_to_disk(output_dir)
    
    print(f"Dataset saved to {output_dir}")


def load_from_disk(name):
    """Load dataset from disk."""
    from datasets import load_from_disk
    return load_from_disk(os.path.join(PROCESSED_DIR, name))


def get_dataset_stats(dataset):
    """Compute dataset statistics."""
    if isinstance(dataset, dict):
        stats = {}
        for split, data in dataset.items():
            stats[split] = len(data)
        return stats
    return {'total': len(dataset)}


def prepare_imdb_for_training(tokenizer, max_length=512):
    """Prepare IMDb dataset for training."""
    dataset = load_imdb_dataset()
    
    def tokenize_function(examples):
        return tokenizer.encode(
            examples['text'],
            max_length=max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
    
    # Remove unnecessary columns
    dataset = dataset.remove_columns(['text'])
    dataset = dataset.rename_columns({'label': 'labels'})
    
    # Tokenize
    tokenized_dataset = dataset.map(
        tokenize_function,
        batched=True,
        batch_size=32,
        desc="Tokenizing"
    )
    
    return tokenized_dataset


def main():
    """Main data preparation pipeline."""
    ensure_dirs()
    
    # Load and inspect IMDb
    print("=" * 60)
    print("IMDB DATASET")
    print("=" * 60)
    imdb_dataset = load_imdb_dataset()
    inspect_dataset(imdb_dataset, "IMDb")
    
    # Load and inspect SST-2
    print("\n" + "=" * 60)
    print("SST-2 DATASET")
    print("=" * 60)
    sst2_dataset = load_sst2_dataset()
    inspect_dataset(sst2_dataset, "SST-2")
    
    # Load and inspect AG News
    print("\n" + "=" * 60)
    print("AG NEWS DATASET")
    print("=" * 60)
    ag_news_dataset = load_ag_news_dataset()
    inspect_dataset(ag_news_dataset, "AG News")
    
    # Load and inspect WNUT NER
    print("\n" + "=" * 60)
    print("WNUT NER DATASET")
    print("=" * 60)
    wnut_dataset = load_wnut_ner_dataset()
    inspect_dataset(wnut_dataset, "WNUT NER")
    
    print("\n" + "=" * 60)
    print("Data preparation complete!")
    print("=" * 60)
    print("Next steps:")
    print("  1. Use src/preprocessing.py to clean text")
    print("  2. Use src/tokenizer.py to tokenize texts")
    print("  3. Use src/transformer modules for model building")


if __name__ == "__main__":
    main()
