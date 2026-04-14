from abc import ABC, abstractmethod

class BaseAIProvider(ABC):
    name = "base"

    @abstractmethod
    def generate_text(self, prompt: str, data: dict):
        raise NotImplementedError

    @abstractmethod
    def generate_images(self, prompt: str, image_paths: list[str], output_count: int = 1):
        raise NotImplementedError
