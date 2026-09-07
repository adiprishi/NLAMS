from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    path('login/', views.login_page, name='login'),

    path('supabase-login/', views.supabase_login, name='supabase_login'),

    path('logout/', views.logout_user, name='logout'),

    path('projects/', views.projects, name='projects'),

    path('projects/create/', views.create_project, name='create_project'),

    path('projects/<int:project_id>/', views.project_detail, name='project_detail'),

    path('reports/', views.reports, name='reports'),

    path(
    'projects/<int:project_id>/workflow/',
    views.project_workflow,
    name='project_workflow'
),

path(
    'projects/<int:project_id>/workflow/rr/',
    views.complete_rr,
    name='complete_rr'
),

path(
    
    'projects/<int:project_id>/workflow/possession/',
    views.complete_possession,
    name='complete_possession'
),

path(
    'projects/<int:project_id>/workflow/action/',
    views.workflow_action,
    name='workflow_action'
),

path(
    'compensation/<int:compensation_id>/pay/',
    views.process_payment,
    name='process_payment'
),

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