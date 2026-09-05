from django.db import models  # pyright: ignore[reportMissingImports]


class Project(models.Model):

    STATUS_CHOICES = [
        ('SUBMITTED', 'Submitted'),
        ('UNDER_REVIEW', 'Under Review'),
        ('APPROVED', 'Approved'),
        ('ACQUISITION', 'Acquisition'),
        ('COMPLETED', 'Completed'),
    ]

    project_name = models.CharField(max_length=200)

    project_type = models.CharField(max_length=100)

    state = models.CharField(max_length=100)

    district = models.CharField(max_length=100)

    land_required = models.DecimalField(max_digits=10, decimal_places=2)

    description = models.TextField(blank=True)

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='SUBMITTED'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.project_name


class LandParcel(models.Model):

    ACQUISITION_STATUS = [
        ('IDENTIFIED', 'Identified'),
        ('VERIFIED', 'Verified'),
        ('NOTIFIED', 'Notified'),
        ('ACQUIRED', 'Acquired'),
        ('POSSESSION', 'Possession Taken'),
    ]

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='parcels'
    )

    parcel_id = models.CharField(max_length=100)

    owner_name = models.CharField(max_length=200)

    area = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=6
    )

    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=6
    )

    status = models.CharField(
        max_length=30,
        choices=ACQUISITION_STATUS,
        default='IDENTIFIED'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.parcel_id

class Compensation(models.Model):

    PAYMENT_STATUS = [
        ('PENDING', 'Pending'),
        ('PARTIAL', 'Partially Paid'),
        ('PAID', 'Fully Paid'),
    ]

    parcel = models.ForeignKey(
        LandParcel,
        on_delete=models.CASCADE,
        related_name='compensation'
    )

    assessed_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2
    )

    paid_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS,
        default='PENDING'
    )

    payment_date = models.DateField(
        null=True,
        blank=True
    )

    remarks = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.parcel.parcel_id} - Compensation"

    @property
    def remaining_amount(self):
        return self.assessed_amount - self.paid_amount

class RRCase(models.Model):

    REHABILITATION_STATUS = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
    ]

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='rr_cases'
    )

    family_id = models.CharField(max_length=100)
    family_name = models.CharField(max_length=200)

    displaced = models.BooleanField(default=False)

    rehabilitation_status = models.CharField(
        max_length=30,
        choices=REHABILITATION_STATUS,
        default='PENDING'
    )

    assistance_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )

    remarks = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.family_id} - {self.family_name}"

class Possession(models.Model):

    POSSESSION_STATUS = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('TAKEN', 'Possession Taken'),
    ]

    parcel = models.ForeignKey(
        LandParcel,
        on_delete=models.CASCADE,
        related_name='possession'
    )

    possession_status = models.CharField(
        max_length=30,
        choices=POSSESSION_STATUS,
        default='PENDING'
    )

    possession_date = models.DateField(
        null=True,
        blank=True
    )

    remarks = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.parcel.parcel_id} - Possession"