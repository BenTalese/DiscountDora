from abc import ABC, abstractmethod


class IProductImageProvider(ABC):

    @abstractmethod
    def get_image(self, image_uri: str):
        pass
