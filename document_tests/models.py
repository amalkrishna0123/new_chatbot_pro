from django.db import models


class UAEDocumentVisa(models.Model):
    """
    Lightweight OCR storage model for testing UAE visa extraction.
    This model is intentionally decoupled from users, chat, and insurance.
    """

    id_number = models.CharField(max_length=50, blank=True, null=True)
    file_number = models.CharField(max_length=50, blank=True, null=True)
    passport_no = models.CharField(max_length=50, blank=True, null=True)
    employer_name = models.CharField(max_length=200, blank=True, null=True)
    uid_no = models.CharField(max_length=50, blank=True, null=True)

    issuing_date = models.CharField(max_length=50, blank=True, null=True)
    expiry_date = models.CharField(max_length=50, blank=True, null=True)

    raw_text = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"UAE Visa ({self.file_number or 'N/A'})"
