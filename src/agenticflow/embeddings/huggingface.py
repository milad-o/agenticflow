"""
HuggingFace Embedding Provider
=============================

Implementation of HuggingFace embedding models using the transformers library
and sentence-transformers for optimized sentence embeddings.
"""

import os
from typing import Any, Dict, List, Optional
import warnings

import structlog

from .base import (
    AsyncEmbeddingProvider,
    EmbeddingConfig,
    EmbeddingProvider,
    EmbeddingTaskType,
    EmbeddingModelNotFoundError,
    EmbeddingProviderNotAvailableError,
)

logger = structlog.get_logger(__name__)


class HuggingFaceEmbeddingProvider(AsyncEmbeddingProvider):
    """HuggingFace embedding provider supporting sentence-transformers and transformers models."""
    
    # Popular model configurations
    MODEL_INFO = {
        "sentence-transformers/all-MiniLM-L6-v2": {
            "dimension": 384,
            "max_input_length": 256,
            "type": "sentence-transformers",
        },
        "sentence-transformers/all-mpnet-base-v2": {
            "dimension": 768,
            "max_input_length": 384,
            "type": "sentence-transformers",
        },
        "sentence-transformers/all-distilroberta-v1": {
            "dimension": 768,
            "max_input_length": 512,
            "type": "sentence-transformers",
        },
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2": {
            "dimension": 384,
            "max_input_length": 128,
            "type": "sentence-transformers",
        },
        "BAAI/bge-small-en-v1.5": {
            "dimension": 384,
            "max_input_length": 512,
            "type": "sentence-transformers",
        },
        "BAAI/bge-base-en-v1.5": {
            "dimension": 768,
            "max_input_length": 512,
            "type": "sentence-transformers",
        },
        "BAAI/bge-large-en-v1.5": {
            "dimension": 1024,
            "max_input_length": 512,
            "type": "sentence-transformers",
        },
    }
    
    def __init__(self, config: EmbeddingConfig):
        super().__init__(config)
        
        self.model = None
        self.tokenizer = None
        self.device = "cpu"  # Default to CPU
        
        # Check for GPU availability
        try:
            import torch
            if torch.cuda.is_available():
                self.device = "cuda"
                self.logger.info(f"Using GPU device: {torch.cuda.get_device_name()}")
        except ImportError:
            pass
        
        # Initialize model
        self._load_model()
    
    def _load_model(self):
        """Load the HuggingFace model."""
        model_name = self.config.model
        
        # Try sentence-transformers first (recommended for embeddings)
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore[import-untyped]
            
            self.model = SentenceTransformer(
                model_name,
                device=self.device,
                cache_folder=os.getenv("HF_CACHE_DIR")
            )
            self._model_type = "sentence-transformers"
            self.logger.info(f"Loaded sentence-transformers model: {model_name}")
            return
            
        except ImportError:
            self.logger.warning("sentence-transformers not available, falling back to transformers")
        except Exception as e:
            self.logger.warning(f"Failed to load with sentence-transformers: {e}")
        
        # Fallback to transformers
        try:
            from transformers import AutoModel, AutoTokenizer  # type: ignore[import-untyped]
            import torch  # type: ignore[import-untyped]
            
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                cache_dir=os.getenv("HF_CACHE_DIR")
            )
            self.model = AutoModel.from_pretrained(
                model_name,
                cache_dir=os.getenv("HF_CACHE_DIR")
            ).to(self.device)
            self._model_type = "transformers"
            self.logger.info(f"Loaded transformers model: {model_name}")
            
        except ImportError:
            raise EmbeddingProviderNotAvailableError(
                "Neither sentence-transformers nor transformers library available. "
                "Install with: pip install sentence-transformers or pip install transformers torch"
            )
        except Exception as e:
            raise EmbeddingModelNotFoundError(f"Failed to load model {model_name}: {e}")
    
    @property
    def supports_batch(self) -> bool:
        """HuggingFace supports batch embedding."""
        return True
    
    @property
    def max_batch_size(self) -> int:
        """HuggingFace batch size (configurable)."""
        return self.config.batch_size
    
    @property
    def max_text_length(self) -> int:
        """Maximum text length for HuggingFace models."""
        model_info = self.MODEL_INFO.get(self.config.model, {})
        return model_info.get("max_input_length", 512) * 4  # chars per token approx
    
    async def _embed_texts_impl(
        self, 
        texts: List[str],
        task_type: Optional[EmbeddingTaskType] = None
    ) -> List[List[float]]:
        """Implementation-specific embedding method."""
        import asyncio
        
        if self._model_type == "sentence-transformers":
            return await self._embed_with_sentence_transformers(texts)
        else:
            return await self._embed_with_transformers(texts)
    
    async def _embed_with_sentence_transformers(self, texts: List[str]) -> List[List[float]]:
        """Embed texts using sentence-transformers."""
        import asyncio
        
        def _encode():
            # Use sentence-transformers encode method
            embeddings = self.model.encode(
                texts,
                show_progress_bar=False,
                convert_to_tensor=False,
                normalize_embeddings=True  # Normalize by default
            )
            return embeddings.tolist() if hasattr(embeddings, 'tolist') else embeddings
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(None, _encode)
        return embeddings
    
    async def _embed_with_transformers(self, texts: List[str]) -> List[List[float]]:
        """Embed texts using transformers (mean pooling)."""
        import asyncio
        import torch
        
        def _encode():
            # Tokenize texts
            encoded_input = self.tokenizer(
                texts,
                padding=True,
                truncation=True,
                return_tensors='pt',
                max_length=self.max_text_length // 4  # approx tokens
            ).to(self.device)
            
            # Get model outputs
            with torch.no_grad():
                model_output = self.model(**encoded_input)
            
            # Perform mean pooling
            token_embeddings = model_output.last_hidden_state
            input_mask_expanded = encoded_input['attention_mask'].unsqueeze(-1).expand(token_embeddings.size()).float()
            
            # Mean pooling with attention mask
            sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
            sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
            embeddings = sum_embeddings / sum_mask
            
            # Normalize embeddings
            embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
            
            return embeddings.cpu().tolist()
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(None, _encode)
        return embeddings
    
    async def get_dimension(self) -> int:
        """Get the embedding dimension."""
        if self._dimension is None:
            # Get from model info or test embedding
            model_info = self.MODEL_INFO.get(self.config.model)
            if model_info:
                self._dimension = model_info["dimension"]
            else:
                # Get dimension from test embedding
                test_embeddings = await self._embed_texts_impl(["test"])
                self._dimension = len(test_embeddings[0])
        
        return self._dimension
    
    async def is_available(self) -> bool:
        """Check if the HuggingFace model is available."""
        try:
            if self.model is None:
                return False
            
            # Test embedding
            await self._embed_texts_impl(["test"])
            return True
        except Exception as e:
            self.logger.warning(f"HuggingFace model not available: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the HuggingFace model."""
        model_info = self.MODEL_INFO.get(self.config.model, {})
        
        return {
            "provider": EmbeddingProvider.HUGGINGFACE.value,
            "model": self.config.model,
            "model_type": self._model_type,
            "dimension": self._dimension or model_info.get("dimension", "unknown"),
            "max_input_length": model_info.get("max_input_length", 512),
            "device": self.device,
            "supports_batch": self.supports_batch,
            "max_batch_size": self.max_batch_size,
            "max_text_length": self.max_text_length,
            "supports_task_types": False,
            "local_model": True,
            "cost_per_1k_tokens": 0.0,  # Local models are free
        }


def create_huggingface_embedding_provider(
    model: str = "sentence-transformers/all-MiniLM-L6-v2",
    device: Optional[str] = None,
    **kwargs
) -> HuggingFaceEmbeddingProvider:
    """
    Create a HuggingFace embedding provider.
    
    Args:
        model: HuggingFace model name (hub model or local path)
        device: Device to use ('cpu', 'cuda', 'auto')
        **kwargs: Additional configuration options
        
    Returns:
        Configured HuggingFace embedding provider
    """
    config = EmbeddingConfig(
        provider=EmbeddingProvider.HUGGINGFACE,
        model=model,
        **kwargs
    )
    
    return HuggingFaceEmbeddingProvider(config)