from typing import Optional

from pydantic import Field

from app.schemas.common import TolerantModel


class ExtractTextData(TolerantModel):
    text: str = ""
    pages: int = 1
    truncated: bool = False
    format: str = "txt"
    needs_ocr: bool = False
