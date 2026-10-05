from fastapi import APIRouter, UploadFile, File, HTTPException

from models.response_models import UploadResponse


router = APIRouter(
    prefix="/upload",
    tags=["Document Upload"]
)


@router.post("/", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...)
):

    filename = file.filename or "unknown"

    allowed_extensions = {
        ".txt",
        ".pdf"
    }

    extension = ""

    if "." in filename:
        extension = "." + filename.rsplit(".", 1)[1].lower()

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="Only TXT and PDF files are supported."
        )

    content = await file.read()

    if extension == ".txt":

        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            text = content.decode("latin-1")

    elif extension == ".pdf":

        try:
            from io import BytesIO
            from pypdf import PdfReader

            reader = PdfReader(BytesIO(content))

            pages = []

            for page in reader.pages:
                page_text = page.extract_text()

                if page_text:
                    pages.append(page_text)

            text = "\n".join(pages)

        except Exception as error:

            raise HTTPException(
                status_code=400,
                detail=f"Could not read PDF: {error}"
            )

    if not text.strip():
        raise HTTPException(
            status_code=400,
            detail="The uploaded document contains no readable text."
        )

    return UploadResponse(
        filename=filename,
        text=text,
        character_count=len(text)
    )