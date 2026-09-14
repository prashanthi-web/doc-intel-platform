from abc import ABC, abstractmethod

from app.config import get_settings

settings = get_settings()


class EmbeddingProvider(ABC):
    @property
    @abstractmethod
    def dimension(self) -> int: ...

    @property
    @abstractmethod
    def model_name(self) -> str: ...

    @abstractmethod
    def embed_texts(self, texts: list[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]


class LocalEmbeddingProvider(EmbeddingProvider):
    """Runs a sentence-transformers model on CPU, no external API calls or costs."""

    _model = None  # shared across instances so the model loads only once per process

    def __init__(self, model_name: str, dimension: int):
        self._model_name = model_name
        self._dimension = dimension

    def _get_model(self):
        if LocalEmbeddingProvider._model is None:
            from sentence_transformers import SentenceTransformer
            LocalEmbeddingProvider._model = SentenceTransformer(self._model_name)
        return LocalEmbeddingProvider._model

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return self._model_name

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        model = self._get_model()
        # normalize_embeddings=True makes cosine similarity equivalent to a
        # simple dot product, which is what Qdrant computes internally.
        embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        return embeddings.tolist()


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """Same interface, backed by OpenAI's embedding API instead of a local model."""

    def __init__(self, model_name: str, dimension: int, api_key: str):
        self._model_name = model_name
        self._dimension = dimension
        self._api_key = api_key

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return self._model_name

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        from openai import OpenAI
        client = OpenAI(api_key=self._api_key)
        response = client.embeddings.create(model=self._model_name, input=texts)
        return [item.embedding for item in response.data]


_provider_instance: EmbeddingProvider | None = None


def get_embedding_provider() -> EmbeddingProvider:
    """Factory: reads EMBEDDING_PROVIDER from settings, returns the right implementation.
    Cached so the (potentially slow-to-load) model is only instantiated once."""
    global _provider_instance
    if _provider_instance is not None:
        return _provider_instance

    if settings.embedding_provider == "local":
        _provider_instance = LocalEmbeddingProvider(settings.embedding_model_name, settings.embedding_dimension)
    elif settings.embedding_provider == "openai":
        _provider_instance = OpenAIEmbeddingProvider(
            settings.embedding_model_name, settings.embedding_dimension, settings.openai_api_key
        )
    else:
        raise ValueError(f"Unknown embedding provider: {settings.embedding_provider}")

    return _provider_instance