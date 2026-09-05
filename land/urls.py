from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    path('projects/', views.projects, name='projects'),

    path('projects/create/', views.create_project, name='create_project'),

    path('projects/<int:project_id>/', views.project_detail, name='project_detail'),

    path('land-map/', views.land_map, name='land_map'),

    path('land-parcels/', views.land_parcels, name='land_parcels'),

    path('rr/', views.rr_list, name='rr_list'),
    path('rr/create/', views.create_rr, name='create_rr'),

    path(
        'land-parcels/create/',
        views.create_parcel,
        name='create_parcel'
    ),

    path(
        'projects/<int:project_id>/status/',
        views.update_status,
        name='update_status'
    ),
    path(
    'compensation/',
    views.compensation_list,
    name='compensation_list'
    ),

    path(
        'compensation/create/',
        views.create_compensation,
        name='create_compensation'
    ),

        path(
        'possession/',
        views.possession_list,
        name='possession_list'
    ),

    path(
        'possession/create/',
        views.create_possession,
        name='create_possession'
    ),

    
]