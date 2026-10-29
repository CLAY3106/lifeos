import openai
import os

# Create an OpenAI client using the API key from environment variables
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_embedding(text: str) -> list[float]:
    """Convert text to a vector using OpenAI's embedding API."""

    try:
        # Call the OpenAI API to get the embedding for the provided text
        response = client.embeddings.create(
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
        response = client.embeddings.create(
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