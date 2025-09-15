    # TODOV2: vector memory tests mocks

    # Use in memory vector db
    #def mock_connect_to_vector_memory(self, *args, **kwargs):
    #    self.vector_db = QdrantClient(":memory:")
    #monkeypatch.setattr(
    #    VectorMemory, "connect_to_vector_memory", mock_connect_to_vector_memory
    #)