from fastapi import APIRouter, Depends, status, BackgroundTasks
from pydantic.networks import EmailStr

from app.api.deps import get_current_active_superuser
from app.utils import generate_test_email, send_email
from app.models import Message


router = APIRouter(prefix="/utils", tags=["utils"])


@router.post(
    "/test-email/",
    dependencies=[Depends(get_current_active_superuser)],
    status_code=status.HTTP_201_CREATED,
)
def test_email(background_tasks: BackgroundTasks, email_to: EmailStr) -> Message:
    """
    Test emails.
    """
    email_data = generate_test_email(email_to=email_to)
    
    background_tasks.add_task(
        send_email,
        email_to=email_to,
        subject=email_data.subject,
        html_content=email_data.html_content,
    )
    return Message(message="Test email has been sent in the background")


@router.get("/health-check/")
async def health_check() -> bool:
    return True
