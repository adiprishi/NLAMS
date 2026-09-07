from django.shortcuts import render, redirect  # type: ignore[import-not-found]
from django.contrib.auth.decorators import login_required  # type: ignore[import-not-found]
from django.http import JsonResponse  # type: ignore[import-not-found]
from django.contrib.auth import login, logout  # type: ignore[import-not-found]
from django.contrib.auth.models import User  # type: ignore[import-not-found]
from .models import Project, LandParcel, Compensation, RRCase, Possession
from django.db.models import Sum  # type: ignore[import-not-found]
from django.utils import timezone
import os
import base64
import json

def format_indian_currency(value):
    value = int(value or 0)

    s = str(value)

    if len(s) <= 3:
        return f"₹{s}"

    last_three = s[-3:]
    remaining = s[:-3]

    parts = []

    while len(remaining) > 2:
        parts.insert(0, remaining[-2:])
        remaining = remaining[:-2]

    if remaining:
        parts.insert(0, remaining)

    return "₹" + ",".join(parts) + "," + last_three

@login_required
def home(request):

    # =========================
    # PROJECT STATISTICS
    # =========================

    total_projects = Project.objects.count()

    approved_projects = Project.objects.filter(
        status='APPROVED'
    ).count()

    under_review_projects = Project.objects.filter(
        status='UNDER_REVIEW'
    ).count()

    acquisition_projects = Project.objects.filter(
        status='ACQUISITION'
    ).count()


    # =========================
    # LAND STATISTICS
    # =========================

    total_land = LandParcel.objects.aggregate(
    total=Sum('area')
)['total'] or 0

    # Land already acquired or possession taken
    acquired_land = LandParcel.objects.filter(
        status__in=['ACQUIRED', 'POSSESSION']
    ).aggregate(
        total=Sum('area')
    )['total'] or 0

    # Land currently moving through verification/notification
    in_progress_land = LandParcel.objects.filter(
        status__in=['VERIFIED', 'NOTIFIED']
    ).aggregate(
        total=Sum('area')
    )['total'] or 0

    # Land not yet processed
    pending_land = LandParcel.objects.filter(
        status='IDENTIFIED'
    ).aggregate(
        total=Sum('area')
    )['total'] or 0


    # =========================
    # ACQUISITION PROGRESS
    # =========================

    if total_land > 0:

        acquired_percentage = round(
            (float(acquired_land) / float(total_land)) * 100
        )

        in_progress_percentage = round(
            (float(in_progress_land) / float(total_land)) * 100
        )

        pending_percentage = round(
            (float(pending_land) / float(total_land)) * 100
        )

    else:

        acquired_percentage = 0
        in_progress_percentage = 0
        pending_percentage = 0

    acquisition_progress = acquired_percentage

    # =========================
    # COMPENSATION
    # =========================

    total_compensation = Compensation.objects.aggregate(
        total=Sum('paid_amount')
    )['total'] or 0

    formatted_compensation = format_indian_currency(
    total_compensation
)

    assessed_compensation = Compensation.objects.aggregate(
        total=Sum('assessed_amount')
    )['total'] or 0


    # =========================
    # R&R
    # =========================

    total_rr_cases = RRCase.objects.count()

    completed_rr = RRCase.objects.filter(
        rehabilitation_status='COMPLETED'
    ).count()

    in_progress_rr = RRCase.objects.filter(
        rehabilitation_status='IN_PROGRESS'
    ).count()

    pending_rr = RRCase.objects.filter(
        rehabilitation_status='PENDING'
    ).count()


    # =========================
    # POSSESSION
    # =========================

    total_possessions = Possession.objects.count()

    possession_taken = Possession.objects.filter(
        possession_status='TAKEN'
    ).count()

    possession_pending = Possession.objects.filter(
        possession_status='PENDING'
    ).count()

    # =========================
    # ACTION REQUIRED
    # =========================

    verification_pending = LandParcel.objects.filter(
        status='IDENTIFIED'
    ).count()

    notification_pending = LandParcel.objects.filter(
        status='VERIFIED'
    ).count()

    compensation_pending = Compensation.objects.filter(
        payment_status__in=['PENDING', 'PARTIAL']
    ).count()

    rr_action_required = RRCase.objects.filter(
        rehabilitation_status__in=['PENDING', 'IN_PROGRESS']
    ).count()

    possession_action_required = Possession.objects.filter(
        possession_status__in=['PENDING', 'IN_PROGRESS']
    ).count()


    # =========================
    # RECENT PROJECTS
    # =========================

    recent_projects = Project.objects.all().order_by(
        '-created_at'
    )[:5]

        # =========================
    # DASHBOARD STATUS
    # =========================

    completed_projects = Project.objects.filter(
        status='COMPLETED'
    ).count()

    affected_families = RRCase.objects.count()


    # =========================
    # SEND DATA TO DASHBOARD
    # =========================

    return render(request, 'land/dashboard.html', {



        # Projects
        'total_projects': total_projects,

        'approved_projects': approved_projects,

        'under_review_projects': under_review_projects,

        'review_projects': under_review_projects,

        'acquisition_projects': acquisition_projects,

        'completed_projects': completed_projects,

        'affected_families': affected_families,

        # Action Required
        'verification_pending': verification_pending,
        'notification_pending': notification_pending,
        'compensation_pending': compensation_pending,
        'rr_action_required': rr_action_required,
        'possession_action_required': possession_action_required,

        # Land
'total_land': total_land,
'acquired_land': acquired_land,
'acquisition_progress': acquisition_progress,
'acquisition_percentage': acquisition_progress,

# Acquisition percentages
'acquired_percentage': acquired_percentage,
'in_progress_percentage': in_progress_percentage,
'pending_percentage': pending_percentage,

        # Compensation
        'total_compensation': total_compensation,
        'formatted_compensation': formatted_compensation,
        'assessed_compensation': assessed_compensation,

        # R&R
        'total_rr_cases': total_rr_cases,
        'completed_rr': completed_rr,
        'in_progress_rr': in_progress_rr,
        'pending_rr': pending_rr,

        # Possession
        'total_possessions': total_possessions,
        'possession_taken': possession_taken,
        'possession_pending': possession_pending,

        

        # Projects
        'recent_projects': recent_projects,

        # Supabase
        'supabase_url': os.getenv('SUPABASE_URL'),
        'supabase_publishable_key': os.getenv(
            'SUPABASE_PUBLISHABLE_KEY'
        ),
    })

@login_required
def projects(request):
    project_list = Project.objects.all().order_by('-created_at')

    active_projects = project_list.exclude(
        status='COMPLETED'
    ).count()

    completed_projects = project_list.filter(
        status='COMPLETED'
    ).count()

    return render(
        request,
        'land/projects.html',
        {
            'projects': project_list,
            'active_projects': active_projects,
            'completed_projects': completed_projects,
        }
    )

@login_required
def project_workflow(request, project_id):

    project = Project.objects.get(id=project_id)

    parcels = project.parcels.all()

    total_parcels = parcels.count()

    # LAND WORKFLOW
    verified_parcels = parcels.filter(
        status__in=['VERIFIED', 'NOTIFIED', 'ACQUIRED', 'POSSESSION']
    ).count()

    notified_parcels = parcels.filter(
        status__in=['NOTIFIED', 'ACQUIRED', 'POSSESSION']
    ).count()

    acquired_parcels = parcels.filter(
        status__in=['ACQUIRED', 'POSSESSION']
    ).count()

    possession_parcels = parcels.filter(
        status='POSSESSION'
    ).count()

    # COMPENSATION
    compensation_records = Compensation.objects.filter(
        parcel__project=project
    )

    total_compensation = compensation_records.count()

    paid_compensation = compensation_records.filter(
        payment_status='PAID'
    ).count()

    # R&R
    rr_cases = RRCase.objects.filter(project=project)

    total_rr = rr_cases.count()

    completed_rr = rr_cases.filter(
        rehabilitation_status='COMPLETED'
    ).count()

    # POSSESSION
    possession_records = Possession.objects.filter(
        parcel__project=project
    )

    total_possession = possession_records.count()

    taken_possession = possession_records.filter(
        possession_status='TAKEN'
    ).count()

    # AUTOMATIC WORKFLOW

    if total_parcels == 0:

        current_stage = "LAND IDENTIFICATION"
        next_action = "Land parcels need to be identified."

    elif verified_parcels < total_parcels:

        current_stage = "LAND VERIFICATION"
        next_action = "Verify all identified land parcels."

    elif notified_parcels < total_parcels:

        current_stage = "NOTIFICATION"
        next_action = "Issue notification for verified parcels."

    elif total_compensation == 0 or paid_compensation < total_compensation:

        current_stage = "COMPENSATION"
        next_action = "Complete compensation assessment and payment."

    elif acquired_parcels < total_parcels:

        current_stage = "ACQUISITION"
        next_action = "Complete acquisition of all notified parcels."

    elif total_rr == 0 or completed_rr < total_rr:

        current_stage = "R&R"
        next_action = "Complete rehabilitation and resettlement activities."

    elif possession_parcels < total_parcels:

        current_stage = "POSSESSION"
        next_action = "Complete possession of all acquired land parcels."

    else:

        current_stage = "COMPLETED"
        next_action = "All acquisition workflow stages are completed."

    context = {
        'project': project,
        'parcels': parcels,

        'total_parcels': total_parcels,
        'verified_parcels': verified_parcels,
        'notified_parcels': notified_parcels,
        'acquired_parcels': acquired_parcels,
        'possession_parcels': possession_parcels,

        'total_compensation': total_compensation,
        'paid_compensation': paid_compensation,

        'total_rr': total_rr,
        'completed_rr': completed_rr,

        'total_possession': total_possession,
        'taken_possession': taken_possession,

        'current_stage': current_stage,
        'next_action': next_action,
    }

    # Synchronize project status with workflow
    if current_stage == "COMPLETED":
        project.status = "COMPLETED"

    elif current_stage in [
        "COMPENSATION",
        "ACQUISITION",
        "R&R",
        "POSSESSION"
    ]:
        project.status = "ACQUISITION"

    elif current_stage == "LAND VERIFICATION":
        project.status = "UNDER_REVIEW"

    else:
        project.status = "SUBMITTED"

    project.save()

    return render(
        request,
        'land/project_workflow.html',
        context
    )


@login_required
def workflow_action(request, project_id):

    project = Project.objects.get(id=project_id)

    if request.method != 'POST':
        return redirect(
            'project_workflow',
            project_id=project.id
        )

    parcels = project.parcels.all()

    # VERIFICATION → NOTIFICATION
    verified_pending = parcels.filter(
        status='VERIFIED'
    )

    for parcel in verified_pending:
        parcel.status = 'NOTIFIED'
        parcel.save()

    # NOTIFICATION → ACQUISITION
    notified_pending = parcels.filter(
        status='NOTIFIED'
    )

    for parcel in notified_pending:
        parcel.status = 'ACQUIRED'
        parcel.save()

    return redirect(
        'project_workflow',
        project_id=project.id
    )

    # -------------------------
    # LAND WORKFLOW
    # -------------------------

    verified_parcels = parcels.filter(
        status__in=['VERIFIED', 'NOTIFIED', 'ACQUIRED', 'POSSESSION']
    ).count()

    notified_parcels = parcels.filter(
        status__in=['NOTIFIED', 'ACQUIRED', 'POSSESSION']
    ).count()

    acquired_parcels = parcels.filter(
        status__in=['ACQUIRED', 'POSSESSION']
    ).count()

    possession_parcels = parcels.filter(
        status='POSSESSION'
    ).count()


    # -------------------------
    # COMPENSATION
    # -------------------------

    compensation_records = Compensation.objects.filter(
        parcel__project=project
    )

    total_compensation = compensation_records.count()

    paid_compensation = compensation_records.filter(
        payment_status='PAID'
    ).count()


    # -------------------------
    # R&R
    # -------------------------

    rr_cases = RRCase.objects.filter(
        project=project
    )

    total_rr = rr_cases.count()

    completed_rr = rr_cases.filter(
        rehabilitation_status='COMPLETED'
    ).count()


    # -------------------------
    # POSSESSION
    # -------------------------

    possession_records = Possession.objects.filter(
        parcel__project=project
    )

    total_possession = possession_records.count()

    taken_possession = possession_records.filter(
        possession_status='TAKEN'
    ).count()


    # -------------------------
    # AUTOMATIC WORKFLOW
    # -------------------------

    if total_parcels == 0:

        current_stage = "LAND IDENTIFICATION"
        next_action = "Land parcels need to be identified."

    elif verified_parcels < total_parcels:

        current_stage = "LAND VERIFICATION"
        next_action = "Verify all identified land parcels."

    elif notified_parcels < total_parcels:

        current_stage = "NOTIFICATION"
        next_action = "Issue notification for verified parcels."

    elif total_compensation == 0 or paid_compensation < total_compensation:

        current_stage = "COMPENSATION"
        next_action = "Complete compensation assessment and payment."

    elif total_rr == 0 or completed_rr < total_rr:

        current_stage = "R&R"
        next_action = "Complete rehabilitation and resettlement activities."

    elif possession_parcels < total_parcels:
        current_stage = "POSSESSION"
        next_action = "Complete possession of all acquired land parcels."
    else:
        current_stage = "COMPLETED"
        next_action = "All acquisition workflow stages are completed."


    context = {

        'project': project,
        'parcels': parcels,

        'total_parcels': total_parcels,
        'verified_parcels': verified_parcels,
        'notified_parcels': notified_parcels,
        'acquired_parcels': acquired_parcels,
        'possession_parcels': possession_parcels,

        'total_compensation': total_compensation,
        'paid_compensation': paid_compensation,

        'total_rr': total_rr,
        'completed_rr': completed_rr,

        'total_possession': total_possession,
        'taken_possession': taken_possession,

        'current_stage': current_stage,
        'next_action': next_action,
    }

    return render(
        request,
        'land/project_workflow.html',
        context
    )

@login_required
def complete_rr(request, project_id):

    project = Project.objects.get(id=project_id)

    if request.method == 'POST':

        rr_cases = RRCase.objects.filter(
            project=project
        )

        for case in rr_cases:

            case.rehabilitation_status = 'COMPLETED'
            case.save()

    return redirect(
        'project_workflow',
        project_id=project.id
    )

@login_required
def complete_possession(request, project_id):

    project = Project.objects.get(id=project_id)

    if request.method == 'POST':

        parcels = project.parcels.filter(
            status__in=['ACQUIRED', 'POSSESSION']
        )

        for parcel in parcels:

            possession, created = Possession.objects.get_or_create(
                parcel=parcel
            )

            possession.possession_status = 'TAKEN'
            possession.possession_date = timezone.now().date()
            possession.remarks = 'Possession taken through NLAMS workflow.'
            possession.save()

            parcel.status = 'POSSESSION'
            parcel.save()

        # Mark project as completed
        project.status = 'COMPLETED'
        project.save()

    return redirect(
        'project_workflow',
        project_id=project.id
    )
@login_required
def create_project(request):

    if request.method == 'POST':

        project_name = request.POST.get('project_name')
        project_type = request.POST.get('project_type')
        state = request.POST.get('state')
        district = request.POST.get('district')
        land_required = request.POST.get('land_required')
        description = request.POST.get('description')

        Project.objects.create(
            project_name=project_name,
            project_type=project_type,
            state=state,
            district=district,
            land_required=land_required,
            description=description
        )

        return redirect('projects')

    return render(request, 'land/create_project.html')

@login_required
def project_detail(request, project_id):

    return redirect(
        'project_workflow',
        project_id=project_id
    )

@login_required
def update_status(request, project_id):

    project = Project.objects.get(id=project_id)

    if request.method == 'POST':

        new_status = request.POST.get('status')

        project.status = new_status
        project.save()

    return redirect('project_detail', project_id=project.id)

@login_required
def land_map(request):
    parcels = LandParcel.objects.all()
    return render(request, 'land/land_map.html', {'parcels': parcels})

@login_required
def land_parcels(request):
    parcels = LandParcel.objects.all().order_by('-created_at')
    return render(request, 'land/land_parcels.html', {
        'parcels': parcels
    })

@login_required
def process_payment(request, compensation_id):

    compensation = Compensation.objects.get(
        id=compensation_id
    )

    if request.method == 'POST':

        compensation.paid_amount = compensation.assessed_amount
        compensation.payment_status = 'PAID'
        compensation.payment_date = timezone.now().date()

        compensation.save()

    return redirect('project_workflow', compensation.parcel.project.id)


@login_required
def create_parcel(request):

    if request.method == 'POST':

        project_id = request.POST.get('project')
        parcel_id = request.POST.get('parcel_id')
        owner_name = request.POST.get('owner_name')
        area = request.POST.get('area')
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        status = request.POST.get('status')

        project = Project.objects.get(id=project_id)

        LandParcel.objects.create(
            project=project,
            parcel_id=parcel_id,
            owner_name=owner_name,
            area=area,
            latitude=latitude,
            longitude=longitude,
            status=status
        )

        return redirect('land_parcels')

    projects = Project.objects.all()

    return render(request, 'land/create_parcel.html', {
        'projects': projects
    })

@login_required
def compensation_list(request):
    compensations = Compensation.objects.all().order_by('-created_at')

    return render(
        request,
        'land/compensation.html',
        {'compensations': compensations}
    )


@login_required
def create_compensation(request):

    if request.method == 'POST':

        parcel_id = request.POST.get('parcel')
        assessed_amount = request.POST.get('assessed_amount')
        paid_amount = request.POST.get('paid_amount')
        payment_status = request.POST.get('payment_status')
        payment_date = request.POST.get('payment_date')
        remarks = request.POST.get('remarks')

        parcel = LandParcel.objects.get(id=parcel_id)

        Compensation.objects.create(
            parcel=parcel,
            assessed_amount=assessed_amount,
            paid_amount=paid_amount,
            payment_status=payment_status,
            payment_date=payment_date or None,
            remarks=remarks
        )

        return redirect('compensation_list')

    parcels = LandParcel.objects.all()

    return render(
        request,
        'land/create_compensation.html',
        {'parcels': parcels}
    )

@login_required
def rr_list(request):
    rr_cases = RRCase.objects.all().order_by('-created_at')
    return render(request, 'land/rr.html', {
        'rr_cases': rr_cases
    })


@login_required
def create_rr(request):
    if request.method == 'POST':
        project_id = request.POST.get('project')
        family_id = request.POST.get('family_id')
        family_name = request.POST.get('family_name')
        displaced = request.POST.get('displaced') == 'on'
        rehabilitation_status = request.POST.get('rehabilitation_status')
        assistance_amount = request.POST.get('assistance_amount')
        remarks = request.POST.get('remarks')

        project = Project.objects.get(id=project_id)

        RRCase.objects.create(
            project=project,
            family_id=family_id,
            family_name=family_name,
            displaced=displaced,
            rehabilitation_status=rehabilitation_status,
            assistance_amount=assistance_amount or 0,
            remarks=remarks
        )

        return redirect('rr_list')

    projects = Project.objects.all()

    return render(request, 'land/create_rr.html', {
        'projects': projects
    })

@login_required
def possession_list(request):
    possessions = Possession.objects.all().order_by('-created_at')

    taken_count = possessions.filter(
        possession_status='TAKEN'
    ).count()

    pending_count = possessions.filter(
        possession_status__in=['PENDING', 'IN_PROGRESS']
    ).count()

    return render(
        request,
        'land/possession.html',
        {
            'possessions': possessions,
            'taken_count': taken_count,
            'pending_count': pending_count,
        }
    )

@login_required
def create_possession(request):
    if request.method == 'POST':
        parcel_id = request.POST.get('parcel')
        possession_status = request.POST.get('possession_status')
        possession_date = request.POST.get('possession_date')
        remarks = request.POST.get('remarks')

        parcel = LandParcel.objects.get(id=parcel_id)

        Possession.objects.create(
            parcel=parcel,
            possession_status=possession_status,
            possession_date=possession_date or None,
            remarks=remarks
        )

        return redirect('possession_list')

    parcels = LandParcel.objects.all()

    return render(
        request,
        'land/create_possession.html',
        {
            'parcels': parcels,
        }
    )

@login_required
def reports(request):
    projects = Project.objects.all()

    total_projects = projects.count()
    completed_projects = projects.filter(status='COMPLETED').count()
    active_projects = projects.exclude(status='COMPLETED').count()

    total_land = projects.aggregate(
        total=Sum('land_required')
    )['total'] or 0

    parcels = LandParcel.objects.all()

    total_parcels = parcels.count()

    acquired_parcels = parcels.filter(
        status__in=['ACQUIRED', 'POSSESSION']
    ).count()

    possession_parcels = parcels.filter(
        status='POSSESSION'
    ).count()

    compensation = Compensation.objects.all()

    total_assessed = compensation.aggregate(
        total=Sum('assessed_amount')
    )['total'] or 0

    total_paid = compensation.aggregate(
        total=Sum('paid_amount')
    )['total'] or 0

    rr_cases = RRCase.objects.all()

    total_rr = rr_cases.count()

    completed_rr = rr_cases.filter(
        rehabilitation_status='COMPLETED'
    ).count()

    context = {
        'total_projects': total_projects,
        'active_projects': active_projects,
        'completed_projects': completed_projects,

        'total_land': total_land,

        'total_parcels': total_parcels,
        'acquired_parcels': acquired_parcels,
        'possession_parcels': possession_parcels,

        'total_assessed': total_assessed,
        'total_paid': total_paid,

        'total_rr': total_rr,
        'completed_rr': completed_rr,
    }

    return render(
        request,
        'land/reports.html',
        context
    )


def login_page(request):
    return render(request, 'land/login.html', {
        'supabase_url': os.getenv('SUPABASE_URL'),
        'supabase_publishable_key': os.getenv('SUPABASE_PUBLISHABLE_KEY'),
    })

def supabase_login(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST request required'}, status=405)

    token = request.POST.get('access_token')

    if not token:
        return JsonResponse({'error': 'Access token missing'}, status=400)

    try:
        # Decode the JWT payload without requiring an external JWT package.
        payload_segment = token.split('.')[1]
        payload = json.loads(
            base64.urlsafe_b64decode(
                payload_segment + '=' * (-len(payload_segment) % 4)
            )
        )

        email = payload.get('email')

        if not email:
            return JsonResponse(
                {'error': 'Email missing from token'},
                status=401
            )

        user, created = User.objects.get_or_create(
            username=email,
            defaults={
                'email': email
            }
        )

        login(request, user)

        return JsonResponse({
            'success': True
        })

    except Exception:
        return JsonResponse(
            {'error': 'Invalid authentication token'},
            status=401
        )

def logout_user(request):
    logout(request)
    return redirect('login')