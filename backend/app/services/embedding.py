import openai
import os

# Load .env before reading OPENAI_API_KEY
import app.config  # noqa: F401

_client = None


def _get_client() -> openai.OpenAI:
    """
    Create the OpenAI client on first use instead of at import time.

    Creating it lazily means the app still starts (and every non-RAG feature
    keeps working) when OPENAI_API_KEY is missing. The error surfaces only
    when an embedding is actually requested.
    """
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY environment variable is required")
        _client = openai.OpenAI(
            api_key=api_key,
            timeout=10.0,     # fail fast instead of hanging a request
            max_retries=1,    # one retry for transient 429s, then degrade
        )
    return _client

def get_embedding(text: str) -> list[float]:
    """Convert text to a vector using OpenAI's embedding API."""

    try:
        # Call the OpenAI API to get the embedding for the provided text
        response = _get_client().embeddings.create(
            model="text-embedding-3-small",
            input=text
        )

         # Extract the embedding vector from the response
        return response.data[0].embedding

    # rate limit error
    except openai.RateLimitError:
        print("Rate limit exceeded.")
        return []
    # invalid request error
    except openai.AuthenticationError:
        print("Invalid API key.")
        return []
    # other errors
    except Exception as e:
        print(f"Embedding error: {e}")
        return []
    
def get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """Convert a list of texts to vectors using OpenAI's embedding API."""

    try:
        # Call the OpenAI API to get embeddings for the provided list of texts
        response = _get_client().embeddings.create(
            model="text-embedding-3-small",
            input=texts
        )

        # Extract the embedding vectors from the response
        return [item.embedding for item in sorted(response.data, key=lambda x: x.index)]

    # rate limit error
    except openai.RateLimitError:
        print("Rate limit exceeded.")
        return []
    # invalid request error
    except openai.AuthenticationError:
        print("Invalid API key.")
        return []
    # other errors
    except Exception as e:
        print(f"Batch embedding error: {e}")
        return [[] for _ in texts]  # Return empty lists matching input length