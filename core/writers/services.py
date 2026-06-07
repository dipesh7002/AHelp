from django.conf import settings
from django.core.mail import EmailMessage


def send_writer_application_email(writer_profile):
    user = writer_profile.user
    subject_names = ", ".join(writer_profile.subjects.values_list("name", flat=True)) or "None selected"
    service_names = ", ".join(writer_profile.services.values_list("name", flat=True)) or "None selected"
    body = "\n".join(
        [
            "A writer submitted their profile for approval.",
            "",
            f"Name: {user.full_name}",
            f"Email: {user.email}",
            f"Headline: {writer_profile.headline or 'Not provided'}",
            f"Bio: {writer_profile.bio or 'Not provided'}",
            f"Languages: {writer_profile.languages or 'Not provided'}",
            f"Location: {user.location or 'Not provided'}",
            f"Education: {writer_profile.education}",
            f"Subjects: {subject_names}",
            f"Services: {service_names}",
            f"Available: {'Yes' if writer_profile.is_available else 'No'}",
            f"Approval status: {writer_profile.get_approval_status_display()}",
            "",
            "Review and approve/reject this writer from the Django admin panel.",
        ]
    )
    message = EmailMessage(
        subject="New writer application",
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[settings.WRITER_APPLICATION_TO_EMAIL],
    )
    if writer_profile.cv:
        message.attach_file(writer_profile.cv.path)
    message.send(fail_silently=False)
