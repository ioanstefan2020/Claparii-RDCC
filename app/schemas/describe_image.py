from typing import Literal, Optional

from app.schemas.common import TolerantModel

DescribeImagePurpose = Literal["alt_text", "read_text", "chart", "document"]


class DescribeImageData(TolerantModel):
    description_ro: str
    text_found: Optional[str] = None
    confidence_note: str = "Descriere generată de AI — verifică datele sau textul important cu o persoană de sprijin."
    purpose: str = "alt_text"
