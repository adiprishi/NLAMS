from django.contrib import admin
from .models import Project, LandParcel, Compensation

admin.site.register(Project)
admin.site.register(LandParcel)
admin.site.register(Compensation)