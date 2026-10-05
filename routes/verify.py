from fastapi import APIRouter

from models.schemas import VerifyRequest
from models.response_models import VerifyResponse

from services.safety import check_safety


router = APIRouter(
    prefix="/verify",
    tags=["Safety"]
)


@router.post("/", response_model=VerifyResponse)
def verify_text(request: VerifyRequest):

    result = check_safety(request.text)

    return VerifyResponse(
        safe=result["safe"],
        level=result["level"],
        keywords=result["keywords"],
        message=result["message"]
    )