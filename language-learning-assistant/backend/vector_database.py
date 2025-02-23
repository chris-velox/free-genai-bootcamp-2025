import os
import json
from typing import Dict, List, Tuple
import shutil  # Import the shutil module
from qdrant_client import QdrantClient, models
from qdrant_client.models import VectorParams, Distance, PointStruct
import numpy as np
import uuid  # Import the uuid module

class VectorDatabaseManager:
    def __init__(self, collection_name: str = "german_learning", dimension: int = 768, qdrant_host: str = "localhost", qdrant_port: int = 6333):
        """
        Initializes the VectorDatabaseManager with a Qdrant client.
        """
        self.collection_name = collection_name
        self.dimension = dimension
        self.client = QdrantClient(path="./qdrant/qdrant.db")

        # Recreate collection if it doesn't exist
        try:
            self.client.recreate_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=self.dimension, distance=Distance.COSINE),
            )
        except Exception as e:
            print(f"Error creating Qdrant collection: {e}")

    def load_structured_data(self, video_id: str, structured_data_dir: str = "structured") -> Tuple[List[str], List[Dict]]:
        """
        Loads structured data from a JSON file.

        Args:
            video_id (str): The ID of the video, used to construct the filename.
            structured_data_dir (str): The directory where structured data JSON files are stored.

        Returns:
            Tuple[List[str], List[Dict]]: A tuple containing lists of text and metadata.
        """
        file_path = os.path.join(structured_data_dir, f"{video_id}.json")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data: Dict = json.load(f)  # type: ignore
            texts = []
            metadatas = []
            for section, questions in data.items():
                for question in questions:
                    text = question.get("text", "")
                    texts.append(text)
                    metadatas.append({
                        "video_id": video_id,
                        "section": section,
                        **question  # type: ignore
                    })
            return texts, metadatas
        except FileNotFoundError:
            print(f"File not found: {file_path}")
            return [], []
        except Exception as e:
            print(f"Error loading structured data: {e}")
            return [], []

    def create_collection(self, collection_name: str):
        """
        Creates a new collection in Qdrant.
        """
        try:
            self.client.recreate_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=self.dimension, distance=Distance.COSINE),
            )
            self.collection_name = collection_name
        except Exception as e:
            print(f"Error creating Qdrant collection: {e}")

    def add_data_to_collection(self, texts: List[str], metadatas: List[Dict], ids: List[str]):
        """
        Adds data to the Qdrant collection.

        Args:
            texts (List[str]): The list of text to add.
            metadatas (List[Dict]): The list of metadata associated with the text.
            ids (List[str]): The list of unique IDs for each text.
        """
        # Assuming you have a function to generate embeddings for the texts
        embeddings = self.generate_embeddings(texts)  # Implement this function

        points = []
        for i, embedding in enumerate(embeddings):
            try:
                # Generate UUID for each point
                point_id = uuid.uuid4()
                point = PointStruct(
                    id=str(point_id),  # Convert UUID to string
                    vector=embedding.tolist(),
                    payload=metadatas[i],
                )
                points.append(point)
            except Exception as e:
                print(f"Error generating point for text: {texts[i]}. Error: {str(e)}")

        try:
            self.client.upsert(
                collection_name=self.collection_name,
                wait=True,
                points=points,
            )
            print(f"Successfully added {len(points)} points to Qdrant collection.")  # Added logging
        except Exception as e:
            print(f"Error adding data to Qdrant collection: {e}")

    def get_collection_size(self) -> int:
        """
        Returns the number of items in the collection.

        Returns:
            int: The number of items in the collection.
        """
        try:
            collection_info = self.client.get_collection(collection_name=self.collection_name)
            return collection_info.vectors_count
        except Exception as e:
            print(f"Error getting Qdrant collection size: {e}")
            return 0

    def query_collection(self, query_texts: List[str], n_results: int = 5):
        """
        Queries the Qdrant collection.

        Args:
            query_texts (List[str]): The list of query texts.
            n_results (int): The number of results to return.

        Returns:
            List: The list of results.
        """
        # Assuming you have a function to generate embeddings for the query texts
        query_embeddings = self.generate_embeddings(query_texts)  # Implement this

        results = []
        for query_embedding in query_embeddings:
            try:
                search_result = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_embedding.tolist(),
                    limit=n_results,
                    with_payload=True
                )
                section_results = []
                for point in search_result:
                    section_results.append({
                        "text": point.payload.get("text", ""),
                        "metadata": point.payload,
                        "score": point.score
                    })
                results.append(section_results)
            except Exception as e:
                print(f"Error querying Qdrant collection: {e}")
                results.append([])
        return results

    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Generates embeddings for the given texts.
        This is a placeholder; replace with your actual embedding generation code.
        """
        num_texts = len(texts)
        embeddings = np.zeros((num_texts, self.dimension), dtype='float32')  # Initialize with zeros

        for i, text in enumerate(texts):
            try:
                # Replace this with your actual embedding generation code
                # For example, you can use Sentence Transformers or OpenAI embeddings
                # This is just a dummy implementation
                embedding = np.random.rand(self.dimension).astype('float32')
                embeddings[i] = embedding
            except Exception as e:
                print(f"Error generating embedding for text: {text}. Error: {e}")
                embeddings[i] = np.zeros(self.dimension, dtype='float32')  # Use zero vector as default
        return embeddings

if __name__ == "__main__":
    # Example Usage
    video_id = "mLUTv35RigE"
    db_manager = VectorDatabaseManager()

    # Load data
    texts, metadatas = db_manager.load_structured_data(video_id, "backend/structured")

    if texts and metadatas:
        # Create a unique ID for each document
        ids = [f"{video_id}_{i}" for i in range(len(texts))]

        # Create a collection (no-op for FAISS)
        collection_name = "german_learning"
        db_manager.create_collection(collection_name)

        # Add data to the collection
        db_manager.add_data_to_collection(texts, metadatas, ids)

        # Verify the collection size
        print(f"Collection size: {db_manager.get_collection_size()}")

        # Query the collection
        query_results = db_manager.query_collection(query_texts=["Was kostet der Pullover?"], n_results=3)
        print(f"Query results: {query_results}")
    else:
        print("No data loaded.") 