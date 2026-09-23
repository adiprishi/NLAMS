from django.contrib.gis.db import models


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

    location = models.PointField(
        geography=True,
        srid=4326,
        null=True,
        blank=True
    )

    boundary_geometry = models.PolygonField(
        geography=True,
        srid=4326,
        null=True,
        blank=True
    )

    boundary = models.JSONField(default=list, blank=True)

    status = models.CharField(
        max_length=30,
        choices=ACQUISITION_STATUS,
        default='IDENTIFIED'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.parcel_id

    @property
    def gis_area_acres(self):
        if not self.boundary_geometry:
            return None

        area_sq_m = self.boundary_geometry.transform(
            32646,
            clone=True
        ).area

        return area_sq_m / 4046.8564224

    @property
    def area_difference_acres(self):
        if self.gis_area_acres is None:
            return None

        return self.gis_area_acres - float(self.area)

    @property
    def has_area_discrepancy(self):
        if self.area_difference_acres is None:
            return False

        return abs(self.area_difference_acres) > 0.01

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
class SitePhoto(models.Model):

    PHOTO_CATEGORY = [
        ('BEFORE', 'Before Acquisition'),
        ('DURING', 'During Acquisition'),
        ('AFTER', 'After Possession'),
        ('SITE', 'Site Condition'),
        ('OTHER', 'Other'),
    ]

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='site_photos'
    )

    parcel = models.ForeignKey(
        LandParcel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='site_photos'
    )

    photo = models.ImageField(
        upload_to='site_photos/'
    )

    category = models.CharField(
        max_length=20,
        choices=PHOTO_CATEGORY,
        default='SITE'
    )

    caption = models.CharField(
        max_length=255,
        blank=True
    )

    uploaded_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.project.project_name} - {self.category}"
    def __str__(self):
        return f"{self.parcel.parcel_id} - Possession"

class AuditLog(models.Model):

    ACTION_CHOICES = [
    ('CREATE', 'Created'),
    ('UPDATE', 'Updated'),
    ('DELETE', 'Deleted'),
    ('UPLOAD', 'Uploaded'),
    ('PAYMENT', 'Payment'),
    ('STATUS_CHANGE', 'Status Change'),
]

    user = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES
    )

    model_name = models.CharField(
        max_length=100
    )

    object_id = models.CharField(
        max_length=100
    )

    description = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.user} - {self.action} - {self.model_name}"