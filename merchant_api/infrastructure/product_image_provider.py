import logging
from base64 import b64encode
from pathlib import Path
from typing import Dict

from merchant_api.infrastructure.configuration_manager import \
    CONFIGURATION_MANAGER
from merchant_api.infrastructure.session import get_cached_session


class ProductImageProvider:

    #region ---------------- Fields ----------------

    _cache_folder: Path
    _image_cache: Dict[str, str] = {}
    _logger: logging.Logger

    #endregion Fields

    #region ---------------- Constructors ----------------

    def __init__(self):
        self._logger = logging.getLogger(__name__)
        # D2: the image cache lives under CACHE_DIR/images so it
        # survives container rebuilds (named volume). The legacy
        # `.image_cache` in the repo root is migrated by
        # path_migration.migrate_legacy_image_cache() on boot.
        self._cache_folder = CONFIGURATION_MANAGER.get_image_cache_dir()

        for _Filename in Path.iterdir(self._cache_folder):
            _Filepath = self._cache_folder / _Filename
            if Path.is_file(_Filepath):
                _ImageUri = self._get_image_uri_from_filename(_Filename)
                with open(_Filepath, "rb") as _File:
                    self._image_cache[_ImageUri] = b64encode(_File.read()).decode('utf-8')

    #endregion Constructors

    #region ---------------- Methods ----------------

    def get_image(self, image_uri: str) -> str | None:
        if not image_uri:
            return

        if image_uri in self._image_cache:
            return self._image_cache[image_uri]

        try:
            with get_cached_session() as _Session:
                _Response = _Session.get(image_uri)
                _RawImageData = _Response.content
                _ImageData = b64encode(_Response.content).decode('utf-8')
                self._image_cache[image_uri] = _ImageData
                self._save_image_to_cache(image_uri, _RawImageData)
                return _ImageData

        except Exception:
            self._logger.exception(f"Encountered a problem grabbing image for product with image URI: {image_uri}")

    def _get_image_uri_from_filename(self, filename: Path):
        return filename.name.replace("_", "/")

    def _get_filename_from_image_uri(self, image_uri: str):
        return image_uri.replace("/", "_")

    def _save_image_to_cache(self, image_uri, image_data):
        _Filename = self._get_filename_from_image_uri(image_uri)
        _Filepath = Path(self._cache_folder) / _Filename
        with open(_Filepath, "wb") as file:
            file.write(image_data)

    #endregion Methods


PRODUCT_IMAGE_PROVIDER = ProductImageProvider()
