from django.shortcuts import render, redirect, get_object_or_404  # type: ignore[import-not-found]
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.geos import Point, Polygon
from django.contrib.auth.decorators import login_required  # type: ignore[import-not-found]
from django.http import JsonResponse, HttpResponse  # type: ignore[import-not-found]
from django.contrib.auth import login, logout  # type: ignore[import-not-found]
from django.contrib.auth.models import User  # type: ignore[import-not-found]
from .utils import log_audit
from .models import OfficerProfile
from .decorators import (
    role_required,
    jurisdiction_required,
    check_project_jurisdiction,
)
from .models import (
    Project,
    LandParcel,
    Compensation,
    RRCase,
    Possession,
    SitePhoto,
    AuditLog
)
import jwt
from jwt import PyJWKClient
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.db.models import Sum  # type: ignore[import-not-found]
from django.utils import timezone
from django.views.decorators.http import require_POST
from elevenlabs.client import ElevenLabs
import os
import base64
import json

elevenlabs_client = ElevenLabs(
    api_key=os.getenv("ELEVENLABS_API_KEY")
)

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

def land_intelligence(request):

    if request.method == 'POST':

        try:
            data = json.loads(request.body)

            geometry_data = data.get('geometry')

            if not geometry_data:
                return JsonResponse(
                    {'error': 'No geometry provided'},
                    status=400
                )

            geometry = GEOSGeometry(
                json.dumps(geometry_data),
                srid=4326
            )

            parcels = LandParcel.objects.filter(
                boundary_geometry__intersects=geometry
            ).select_related('project')

            results = []

            for parcel in parcels:
                results.append({
    'parcel_id': parcel.parcel_id,
    'owner_name': parcel.owner_name,
    'area': float(parcel.area),
    'status': parcel.status,
    'geometry': json.loads(
        parcel.boundary_geometry.geojson
    ) if parcel.boundary_geometry else None,
})

            return JsonResponse({
                'count': len(results),
                'parcels': results,
            })

        except Exception as e:

            return JsonResponse(
                {'error': str(e)},
                status=400
            )


    parcels = LandParcel.objects.select_related('project').all()

    selected_parcel = None
    compensation_records = []
    possession_record = None
    rr_cases = []

    parcel_id = request.GET.get('parcel')

    if parcel_id:

        selected_parcel = LandParcel.objects.select_related(
            'project'
        ).filter(parcel_id=parcel_id).first()

        if selected_parcel:

            compensation_records = Compensation.objects.filter(
                parcel=selected_parcel
            )

            possession_record = Possession.objects.filter(
                parcel=selected_parcel
            ).first()

            rr_cases = RRCase.objects.filter(
                project=selected_parcel.project
            )

    return render(
        request,
        'land/land_intelligence.html',
        {
            'parcels': parcels,
            'selected_parcel': selected_parcel,
            'compensation_records': compensation_records,
            'possession_record': possession_record,
            'rr_cases': rr_cases,
        }
    )

def officer_login(request):

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)
            return redirect('home')

        return render(request, 'land/officer_login.html', {
            'error': 'Invalid username or password.'
        })

    return render(request, 'land/officer_login.html')

@login_required
def officer_logout(request):
    logout(request)
    return redirect('home')

def project_progress(request, project_id):

    project = get_object_or_404(Project, id=project_id)

    parcels = LandParcel.objects.filter(project=project)

    compensation_records = Compensation.objects.filter(
        parcel__project=project
    )

    rr_cases = RRCase.objects.filter(
        project=project
    )

    possession_records = Possession.objects.filter(
        parcel__project=project
    )

    site_photos = SitePhoto.objects.filter(
    project=project
).select_related(
    'parcel',
    'uploaded_by'
).order_by(
    '-uploaded_at'
)


    # -----------------------------------------
    # PROJECT PROGRESS
    # -----------------------------------------

    status_progress = {
        'SUBMITTED': 15,
        'UNDER_REVIEW': 30,
        'APPROVED': 45,
        'ACQUISITION': 70,
        'COMPLETED': 100,
    }

    progress = status_progress.get(
        project.status,
        0
    )

    # -----------------------------------------
    # PARCEL STATUS COUNTS
    # -----------------------------------------

    total_parcels = parcels.count()

    verified_parcels = parcels.filter(
        status__in=[
            'VERIFIED',
            'NOTIFIED',
            'ACQUIRED',
            'POSSESSION'
        ]
    ).count()

    notified_parcels = parcels.filter(
        status__in=[
            'NOTIFIED',
            'ACQUIRED',
            'POSSESSION'
        ]
    ).count()

    acquired_parcels = parcels.filter(
        status__in=[
            'ACQUIRED',
            'POSSESSION'
        ]
    ).count()

    possession_parcels = parcels.filter(
        status='POSSESSION'
    ).count()

        # -----------------------------------------
    # COST INTELLIGENCE
    # -----------------------------------------

    total_assessed = compensation_records.aggregate(
        total=Sum('assessed_amount')
    )['total'] or 0

    total_paid = compensation_records.aggregate(
        total=Sum('paid_amount')
    )['total'] or 0

    total_pending = total_assessed - total_paid

    if total_pending < 0:
        total_pending = 0

        # -----------------------------------------
    # PROBLEMS & ATTENTION REQUIRED
    # -----------------------------------------

    attention_items = []

    # 1. LAND VERIFICATION
    verification_pending = parcels.filter(
        status='IDENTIFIED'
    ).count()

    if verification_pending > 0:

        attention_items.append({
            'type': 'Land Verification',
            'title': 'Land verification pending',
            'description': (
                f'{verification_pending} parcel(s) '
                'are still awaiting verification.'
            ),
            'severity': 'High'
        })


    # 2. NOTIFICATION
    notification_pending = parcels.filter(
        status='VERIFIED'
    ).count()

    if notification_pending > 0:

        attention_items.append({
            'type': 'Notification',
            'title': 'Land notification pending',
            'description': (
                f'{notification_pending} verified parcel(s) '
                'have not yet reached notification.'
            ),
            'severity': 'Medium'
        })


    # 3. ACQUISITION
    acquisition_pending = parcels.filter(
        status__in=['NOTIFIED']
    ).count()

    if acquisition_pending > 0:

        attention_items.append({
            'type': 'Acquisition',
            'title': 'Acquisition pending',
            'description': (
                f'{acquisition_pending} notified parcel(s) '
                'are awaiting acquisition.'
            ),
            'severity': 'High'
        })


    # 4. COMPENSATION
    compensation_pending = compensation_records.exclude(
        payment_status='PAID'
    ).count()

    if compensation_pending > 0:

        attention_items.append({
            'type': 'Compensation',
            'title': 'Compensation payment pending',
            'description': (
                f'{compensation_pending} compensation '
                'record(s) require payment.'
            ),
            'severity': 'High'
        })


    # 5. R&R
    rr_pending = rr_cases.exclude(
        rehabilitation_status__in=[
            'COMPLETED',
            'COMPLETE',
            'REHABILITATED'
        ]
    ).count()

    if rr_pending > 0:

        attention_items.append({
            'type': 'R&R',
            'title': 'Rehabilitation & Resettlement pending',
            'description': (
                f'{rr_pending} R&R case(s) '
                'require attention.'
            ),
            'severity': 'Medium'
        })


    # 6. POSSESSION
    possession_pending = possession_records.exclude(
        possession_status__in=[
            'TAKEN',
            'POSSESSION',
            'COMPLETED',
            'POSSESSION TAKEN'
        ]
    ).count()

    if possession_pending > 0:

        attention_items.append({
            'type': 'Possession',
            'title': 'Possession pending',
            'description': (
                f'{possession_pending} parcel(s) '
                'are awaiting possession.'
            ),
            'severity': 'High'
        })


    # 7. PROJECT HEALTH
    if not attention_items:

        attention_items.append({
            'type': 'Project Health',
            'title': 'Project is currently on track',
            'description': (
                'No unresolved land, compensation, '
                'R&R or possession issues were detected '
                'in the available project records.'
            ),
            'severity': 'Good'
        })

            # -----------------------------------------
    # NEXT ACTION
    # -----------------------------------------

    if verification_pending > 0:

        next_action = (
            f'Verify {verification_pending} '
            f'identified parcel(s).'
        )

    elif notification_pending > 0:

        next_action = (
            f'Issue notification for '
            f'{notification_pending} verified parcel(s).'
        )

    elif acquisition_pending > 0:

        next_action = (
            f'Complete acquisition for '
            f'{acquisition_pending} notified parcel(s).'
        )

    elif compensation_pending > 0:

        next_action = (
            f'Complete payment for '
            f'{compensation_pending} compensation record(s).'
        )

    elif rr_pending > 0:

        next_action = (
            f'Complete rehabilitation and resettlement '
            f'for {rr_pending} case(s).'
        )

    elif possession_pending > 0:

        next_action = (
            f'Complete possession for '
            f'{possession_pending} parcel(s).'
        )

    else:

        next_action = (
            'No immediate action required. '
            'All tracked acquisition stages are complete.'
        )

    context = {
        'project': project,

        'parcels': parcels,
        'compensation_records': compensation_records,
        'rr_cases': rr_cases,
        'possession_records': possession_records,

        'progress': progress,

        'total_parcels': total_parcels,
        'verified_parcels': verified_parcels,
        'notified_parcels': notified_parcels,
        'acquired_parcels': acquired_parcels,
        'possession_parcels': possession_parcels,
        'attention_items': attention_items,

        'total_assessed': total_assessed,
        'total_paid': total_paid,
        'total_pending': total_pending,
        'next_action': next_action,
        'site_photos': site_photos,
    }

    return render(
        request,
        'land/project_progress.html',
        context
    )

def search(request):
    query = request.GET.get('q', '').strip()

    projects = Project.objects.none()
    parcels = LandParcel.objects.none()

    if query:
        projects = Project.objects.filter(
            Q(project_name__icontains=query) |
            Q(state__icontains=query) |
            Q(district__icontains=query) |
            Q(project_type__icontains=query)
        ).order_by('-created_at')

        parcels = LandParcel.objects.filter(
            Q(parcel_id__icontains=query) |
            Q(owner_name__icontains=query) |
            Q(status__icontains=query)
        ).select_related('project').order_by('-created_at')

    return render(request, 'land/search_results.html', {
        'query': query,
        'projects': projects,
        'parcels': parcels,
    })
@login_required
def text_to_speech(request):
    if request.method != "POST":
        return JsonResponse(
            {"error": "POST request required"},
            status=405
        )

    try:
        data = json.loads(request.body)
        text = data.get("text", "").strip()

        if not text:
            return JsonResponse(
                {"error": "No text provided"},
                status=400
            )

        text = text[:1000]

        print("ElevenLabs request text:", text)
        print("ElevenLabs API key loaded:", bool(os.getenv("ELEVENLABS_API_KEY")))

        audio = elevenlabs_client.text_to_speech.convert(
            text=text,
            voice_id="JBFqnCBsd6RMkjVDRZzb",
            model_id="eleven_flash_v2_5",
            output_format="mp3_44100_128",
        )

        audio_bytes = b"".join(audio)

        print("ElevenLabs audio generated:", len(audio_bytes), "bytes")

        return HttpResponse(
            audio_bytes,
            content_type="audio/mpeg"
        )

    except Exception as e:
        print("================================")
        print("ELEVENLABS ERROR")
        print("TYPE:", type(e).__name__)
        print("STATUS:", getattr(e, "status_code", "N/A"))
        print("BODY:", getattr(e, "body", "N/A"))
        print("ERROR:", str(e))
        print("================================")

    return JsonResponse(
        {"error": str(e)},
        status=500
    )

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

    parcels = LandParcel.objects.exclude(
    location__isnull=True
)


    # =========================
    # SEND DATA TO DASHBOARD
    # =========================

    return render(request, 'land/dashboard_gemini.html', {



        # Projects
        'total_projects': total_projects,

        'approved_projects': approved_projects,

        'under_review_projects': under_review_projects,

        'review_projects': under_review_projects,

        'acquisition_projects': acquisition_projects,

        'completed_projects': completed_projects,

        'affected_families': affected_families,
        'parcels': parcels,

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


def project_workflow(request, project_id):

    project = get_object_or_404(Project, id=project_id)

    parcels = project.parcels.all()

    total_parcels = parcels.count()

    # LAND WORKFLOW
    verified_parcels = parcels.filter(
        status__in=[
            'VERIFIED',
            'NOTIFIED',
            'ACQUIRED',
            'POSSESSION'
        ]
    ).count()

    notified_parcels = parcels.filter(
        status__in=[
            'NOTIFIED',
            'ACQUIRED',
            'POSSESSION'
        ]
    ).count()

    acquired_parcels = parcels.filter(
        status__in=[
            'ACQUIRED',
            'POSSESSION'
        ]
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
    rr_cases = RRCase.objects.filter(
        project=project
    )

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
        next_action = (
            "Complete compensation assessment and payment."
        )

    elif acquired_parcels < total_parcels:

        current_stage = "ACQUISITION"
        next_action = (
            "Complete acquisition of all notified parcels."
        )

    elif total_rr == 0 or completed_rr < total_rr:

        current_stage = "R&R"
        next_action = (
            "Complete rehabilitation and resettlement activities."
        )

    elif possession_parcels < total_parcels:

        current_stage = "POSSESSION"
        next_action = (
            "Complete possession of all acquired land parcels."
        )

    else:

        current_stage = "COMPLETED"
        next_action = (
            "All acquisition workflow stages are completed."
        )

    # -----------------------------------------
    # ATTENTION REQUIRED
    # -----------------------------------------

    attention_items = []

    # Check compensation
    for compensation in compensation_records:

        payment_status = str(
            compensation.payment_status
        ).upper()

        if payment_status != 'PAID':

            attention_items.append({
                'type': 'Compensation',
                'title': 'Compensation payment pending',
                'description': (
                    f'Payment pending for parcel '
                    f'{compensation.parcel.parcel_id}'
                ),
                'severity': 'High'
            })

    # Check possession
    for possession in possession_records:

        possession_status = str(
            possession.possession_status
        ).upper()

        if possession_status not in [
            'TAKEN',
            'POSSESSION',
            'COMPLETED',
            'POSSESSION TAKEN'
        ]:

            attention_items.append({
                'type': 'Possession',
                'title': 'Possession pending',
                'description': (
                    f'Possession issue for parcel '
                    f'{possession.parcel.parcel_id}'
                ),
                'severity': 'High'
            })

    # Check R&R
    for rr in rr_cases:

        rehabilitation_status = str(
            rr.rehabilitation_status
        ).upper()

        if rehabilitation_status not in [
            'COMPLETED',
            'COMPLETE',
            'REHABILITATED'
        ]:

            attention_items.append({
                'type': 'R&R',
                'title': 'Rehabilitation pending',
                'description': (
                    f'R&R case {rr.family_id} '
                    f'requires attention'
                ),
                'severity': 'Medium'
            })

    # -----------------------------------------
    # DISPLAY STATUS
    # -----------------------------------------
    #
    # IMPORTANT:
    # This is calculated for display only.
    # We DO NOT save it to the database here.
    #

    if current_stage == "COMPLETED":

        workflow_status = "COMPLETED"

    elif current_stage in [
        "COMPENSATION",
        "ACQUISITION",
        "R&R",
        "POSSESSION"
    ]:

        workflow_status = "ACQUISITION"

    elif current_stage == "LAND VERIFICATION":

        workflow_status = "UNDER_REVIEW"

    else:

        workflow_status = "SUBMITTED"

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
        'attention_items': attention_items,

        # Calculated display status.
        'workflow_status': workflow_status,
    }

    return render(
        request,
        'land/project_workflow.html',
        context
    )
@jurisdiction_required
@role_required('ADMIN', 'CENTRAL', 'STATE', 'DISTRICT')
def workflow_action(request, project_id):

    project = get_object_or_404(
        Project,
        id=project_id
    )

    if request.method != 'POST':
        return redirect(
            'project_workflow',
            project_id=project.id
        )

    parcels = project.parcels.all()

    # -------------------------------------------------
    # VERIFIED → NOTIFIED
    # -------------------------------------------------

    verified_pending = parcels.filter(
        status='VERIFIED'
    )

    if verified_pending.exists():

        for parcel in verified_pending:

            old_status = parcel.status

            parcel.status = 'NOTIFIED'

            parcel.save(
                update_fields=['status']
            )

            log_audit(
                user=request.user,
                action='UPDATE',
                instance=parcel,
                description=(
                    f'Changed parcel status from '
                    f'"{old_status}" to "NOTIFIED" '
                    f'for parcel "{parcel.parcel_id}" '
                    f'in project "{project.project_name}".'
                )
            )

        return redirect(
            'project_workflow',
            project_id=project.id
        )

    # -------------------------------------------------
    # NOTIFIED → ACQUIRED
    # -------------------------------------------------

    notified_pending = parcels.filter(status='NOTIFIED')
    if notified_pending.exists():
        for parcel in notified_pending:
            old_status = parcel.status
            parcel.status = 'ACQUIRED'
            parcel.save(update_fields=['status'])

            log_audit(
                user=request.user,
                action='STATUS_CHANGE',
                instance=parcel,
                description=(
                    f'Changed parcel status from "{old_status}" to "ACQUIRED" '
                    f'for parcel "{parcel.parcel_id}" in project "{project.project_name}".'
                )
            )

        # Update the project stage when acquisition is reached
        old_project_status = project.status
        if old_project_status != 'ACQUISITION':
            project.status = 'ACQUISITION'
            project.save(update_fields=['status'])

            log_audit(
                user=request.user,
                action='STATUS_CHANGE',
                instance=project,
                description=(
                    f'Project "{project.project_name}" status changed from '
                    f'"{old_project_status}" to "ACQUISITION" after land parcels '
                    f'were acquired.'
                )
            )

        return redirect('project_workflow', project_id=project.id)
    # -------------------------------------------------
    # Nothing to advance
    # -------------------------------------------------

    return redirect(
        'project_workflow',
        project_id=project.id
    )

@role_required('ADMIN', 'CENTRAL', 'STATE', 'DISTRICT')
def complete_rr(request, project_id):

    project = get_object_or_404(
        Project,
        id=project_id
    )

    if request.method != 'POST':
        return redirect(
            'project_workflow',
            project_id=project.id
        )

    rr_cases = RRCase.objects.filter(
        project=project
    )

    for case in rr_cases:

        old_status = case.rehabilitation_status

        # Don't create duplicate audit records
        # for cases already completed.
        if str(old_status).upper() in [
            'COMPLETED',
            'COMPLETE',
            'REHABILITATED'
        ]:
            continue

        case.rehabilitation_status = 'COMPLETED'

        case.save(
            update_fields=[
                'rehabilitation_status'
            ]
        )

        log_audit(
            user=request.user,
            action='STATUS_CHANGE',
            instance=case,
            description=(
                f'Changed R&R rehabilitation status from '
                f'"{old_status}" to "COMPLETED" for family '
                f'"{case.family_id}" in project '
                f'"{project.project_name}".'
            )
        )

    return redirect(
        'project_workflow',
        project_id=project.id
    )

@role_required('ADMIN', 'CENTRAL', 'STATE', 'DISTRICT')
def complete_possession(request, project_id):

    project = get_object_or_404(
        Project,
        id=project_id
    )

    if request.method != 'POST':
        return redirect(
            'project_workflow',
            project_id=project.id
        )

    parcels = project.parcels.filter(
        status__in=['ACQUIRED', 'POSSESSION']
    )

    for parcel in parcels:

        possession, created = Possession.objects.get_or_create(
            parcel=parcel
        )

        old_possession_status = possession.possession_status
        old_parcel_status = parcel.status

        # -------------------------
        # POSSESSION RECORD
        # -------------------------

        if old_possession_status != 'TAKEN':

            possession.possession_status = 'TAKEN'
            possession.possession_date = timezone.now().date()
            possession.remarks = (
                'Possession taken through NLAMS workflow.'
            )

            possession.save(
                update_fields=[
                    'possession_status',
                    'possession_date',
                    'remarks'
                ]
            )

            log_audit(
                user=request.user,
                action='STATUS_CHANGE',
                instance=possession,
                description=(
                    f'Changed possession status for parcel '
                    f'"{parcel.parcel_id}" from '
                    f'"{old_possession_status}" to "TAKEN" '
                    f'in project '
                    f'"{project.project_name}".'
                )
            )

        # -------------------------
        # LAND PARCEL STATUS
        # -------------------------

        if old_parcel_status != 'POSSESSION':

            parcel.status = 'POSSESSION'

            parcel.save(
                update_fields=[
                    'status'
                ]
            )

            log_audit(
                user=request.user,
                action='STATUS_CHANGE',
                instance=parcel,
                description=(
                    f'Changed land parcel status for '
                    f'"{parcel.parcel_id}" from '
                    f'"{old_parcel_status}" to "POSSESSION" '
                    f'in project '
                    f'"{project.project_name}".'
                )
            )

    # -------------------------
    # PROJECT COMPLETION
    # -------------------------

    old_project_status = project.status

    if old_project_status != 'COMPLETED':

        project.status = 'COMPLETED'

        project.save(
            update_fields=[
                'status'
            ]
        )

        log_audit(
            user=request.user,
            action='STATUS_CHANGE',
            instance=project,
            description=(
                f'Project "{project.project_name}" status '
                f'changed from "{old_project_status}" '
                f'to "COMPLETED" after possession was taken '
                f'for all acquired parcels.'
            )
        )

    return redirect(
        'project_workflow',
        project_id=project.id
    )
@role_required('ADMIN', 'CENTRAL', 'STATE', 'DISTRICT')
def create_project(request):

    if request.method == 'POST':

        project_name = request.POST.get('project_name')
        project_type = request.POST.get('project_type')
        state = request.POST.get('state')
        district = request.POST.get('district')

        profile = request.user.officer_profile

        if profile.role == 'STATE':
            if profile.state.strip().lower() != state.strip().lower():
                messages.error(
                    request,
                    'You can only create projects within your assigned state.'
                )
                return redirect('create_project')

        elif profile.role == 'DISTRICT':
            if (
                profile.state.strip().lower() != state.strip().lower()
                or
                profile.district.strip().lower() != district.strip().lower()
            ):
                messages.error(
                    request,
                    'You can only create projects within your assigned district.'
                )
                return redirect('create_project')

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


def project_detail(request, project_id):

    return redirect(
        'project_workflow',
        project_id=project_id
    )

@jurisdiction_required
@role_required('ADMIN', 'CENTRAL', 'STATE')
def update_status(request, project_id):

    project = Project.objects.get(id=project_id)

    if request.method == 'POST':

        new_status = request.POST.get('status')

        project.status = new_status
        project.save()

    return redirect('project_detail', project_id=project.id)


def land_map(request):

    project_id = request.GET.get('project')

    if project_id:
        project = get_object_or_404(
            Project,
            id=project_id
        )

        parcels = LandParcel.objects.filter(
            project=project
        ).prefetch_related('compensation')

        page_title = project.project_name

    else:
        project = None

        parcels = LandParcel.objects.all().prefetch_related(
            'compensation'
        )

        page_title = 'All Projects'

    return render(
        request,
        'land/land_map.html',
        {
            'parcels': parcels,
            'project': project,
            'page_title': page_title,
        }
    )


@login_required
def land_parcels(request):

    profile = getattr(request.user, 'officer_profile', None)

    if not profile:
        messages.error(
            request,
            'Officer profile not found.'
        )
        return redirect('home')

    if profile.role in ['ADMIN', 'CENTRAL']:

        parcels = LandParcel.objects.all().order_by('-created_at')

    elif profile.role == 'STATE':

        parcels = LandParcel.objects.filter(
            project__state__iexact=profile.state
        ).order_by('-created_at')

    elif profile.role == 'DISTRICT':

        parcels = LandParcel.objects.filter(
            project__state__iexact=profile.state,
            project__district__iexact=profile.district
        ).order_by('-created_at')

    else:

        # PIA and other read-only users
        parcels = LandParcel.objects.none()

    return render(
        request,
        'land/land_parcels.html',
        {
            'parcels': parcels,
            'can_create': profile.role in [
                'ADMIN',
                'CENTRAL',
                'STATE',
                'DISTRICT'
            ],
        }
    )

@role_required('ADMIN', 'CENTRAL', 'STATE')
def process_payment(request, compensation_id):

    compensation = get_object_or_404(
        Compensation.objects.select_related(
            'parcel',
            'parcel__project'
        ),
        id=compensation_id
    )
    allowed, message = check_project_jurisdiction(
    request,
    compensation.parcel.project
)

    if not allowed:
        messages.error(request, message)
        return redirect(
            'project_workflow',
            project_id=compensation.parcel.project.id
        )

    # Payment changes must only happen through POST.
    if request.method != 'POST':
        return redirect(
            'project_workflow',
            project_id=compensation.parcel.project.id
        )

    # Prevent processing the same payment twice.
    if compensation.payment_status == 'PAID':
        return redirect(
            'project_workflow',
            project_id=compensation.parcel.project.id
        )

    old_status = compensation.payment_status
    old_paid_amount = compensation.paid_amount

    compensation.paid_amount = compensation.assessed_amount
    compensation.payment_status = 'PAID'
    compensation.payment_date = timezone.now().date()

    compensation.save(
        update_fields=[
            'paid_amount',
            'payment_status',
            'payment_date'
        ]
    )

    log_audit(
        user=request.user,
        action='PAYMENT',
        instance=compensation,
        description=(
            f'Processed compensation payment for parcel '
            f'"{compensation.parcel.parcel_id}" in project '
            f'"{compensation.parcel.project.project_name}". '
            f'Payment status changed from "{old_status}" to "PAID". '
            f'Paid amount changed from ₹{old_paid_amount} '
            f'to ₹{compensation.paid_amount}.'
        )
    )

    return redirect(
        'project_workflow',
        project_id=compensation.parcel.project.id
    )

@role_required('ADMIN', 'CENTRAL', 'STATE', 'DISTRICT')
def create_parcel(request):
    if request.method == 'POST':
        project_id = request.POST.get('project')
        parcel_id = request.POST.get('parcel_id')
        owner_name = request.POST.get('owner_name')
        area = request.POST.get('area')
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        status = request.POST.get('status')
        boundary_json = request.POST.get('boundary')
        print("BOUNDARY RECEIVED:", boundary_json)

        project = get_object_or_404(Project, id=project_id)

        allowed, message = check_project_jurisdiction(request, project)

        if not allowed:
            messages.error(request, message)
            return redirect('land_parcels')

        # Create GIS point from latitude/longitude
        location = Point(
            float(longitude),
            float(latitude),
            srid=4326
        )

        # Create GIS polygon if a boundary was drawn
        boundary_geometry = None
        coordinates = []

        if boundary_json:
            try:
                coordinates = json.loads(boundary_json)

                polygon_points = [
                    (float(lng), float(lat))
                    for lat, lng in coordinates
                ]

                if polygon_points[0] != polygon_points[-1]:
                    polygon_points.append(polygon_points[0])

                boundary_geometry = Polygon(
                    polygon_points,
                    srid=4326
                )

            except (ValueError, TypeError, IndexError, json.JSONDecodeError):
                boundary_geometry = None
                coordinates = []

        parcel = LandParcel.objects.create(
            project=project,
            parcel_id=parcel_id,
            owner_name=owner_name,
            area=area,
            latitude=latitude,
            longitude=longitude,
            location=location,
            boundary_geometry=boundary_geometry,
            boundary=coordinates,
            status=status
        )

        log_audit(
            user=request.user,
            action='CREATE',
            instance=parcel,
            description=(
                f'Created land parcel "{parcel.parcel_id}" '
                f'for project "{project.project_name}".'
            )
        )

        return redirect('land_parcels')

    profile = request.user.officer_profile

    if profile.role in ['ADMIN', 'CENTRAL']:

        projects = Project.objects.all()

    elif profile.role == 'STATE':

        projects = Project.objects.filter(
            state__iexact=profile.state
        )

    elif profile.role == 'DISTRICT':

        projects = Project.objects.filter(
            state__iexact=profile.state,
            district__iexact=profile.district
        )

    else:

        projects = Project.objects.none()

    projects = projects.order_by('project_name')

    return render(
        request,
        'land/create_parcel.html',
        {
            'projects': projects
        }
    )

@login_required
def compensation_list(request):

    profile = getattr(request.user, 'officer_profile', None)

    if not profile:
        messages.error(
            request,
            'Officer profile not found.'
        )
        return redirect('home')

    compensations = (
        Compensation.objects
        .select_related('parcel', 'parcel__project')
    )

    if profile.role in ['ADMIN', 'CENTRAL']:

        pass

    elif profile.role == 'STATE':

        compensations = compensations.filter(
            parcel__project__state__iexact=profile.state
        )

    elif profile.role == 'DISTRICT':

        compensations = compensations.filter(
            parcel__project__state__iexact=profile.state,
            parcel__project__district__iexact=profile.district
        )

    else:

        compensations = compensations.none()

    compensations = compensations.order_by('-created_at')

    return render(
        request,
        'land/compensation.html',
        {
            'compensations': compensations,
        }
    )
@role_required('ADMIN', 'CENTRAL', 'STATE', 'DISTRICT')
def create_possession(request):

    if request.method == 'POST':

        parcel_id = request.POST.get('parcel')
        possession_status = request.POST.get('possession_status')
        possession_date = request.POST.get('possession_date')
        remarks = request.POST.get('remarks')

        parcel = get_object_or_404(
            LandParcel,
            id=parcel_id
        )

        allowed, message = check_project_jurisdiction(
            request,
            parcel.project
        )

        if not allowed:
            messages.error(request, message)
            return redirect('possession_list')

        possession = Possession.objects.create(
            parcel=parcel,
            possession_status=possession_status,
            possession_date=possession_date or None,
            remarks=remarks
        )

        log_audit(
            user=request.user,
            action='CREATE',
            instance=possession,
            description=(
                f'Created possession record for parcel '
                f'"{parcel.parcel_id}" in project '
                f'"{parcel.project.project_name}". '
                f'Possession status: '
                f'"{possession_status}".'
            )
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

@role_required('ADMIN', 'CENTRAL', 'STATE', 'DISTRICT')
def create_compensation(request):

    if request.method == 'POST':

        parcel_id = request.POST.get('parcel')
        assessed_amount = request.POST.get('assessed_amount')
        paid_amount = request.POST.get('paid_amount', 0)
        payment_status = request.POST.get('payment_status')
        payment_date = request.POST.get('payment_date')
        remarks = request.POST.get('remarks')

        parcel = get_object_or_404(
            LandParcel.objects.select_related('project'),
            id=parcel_id
        )

        allowed, message = check_project_jurisdiction(
            request,
            parcel.project
        )

        if not allowed:
            messages.error(request, message)
            return redirect('compensation_list')

        compensation = Compensation.objects.create(
            parcel=parcel,
            assessed_amount=assessed_amount,
            paid_amount=paid_amount or 0,
            payment_status=payment_status,
            payment_date=payment_date or None,
            remarks=remarks
        )

        log_audit(
            user=request.user,
            action='CREATE',
            instance=compensation,
            description=(
                f'Created compensation record for parcel '
                f'"{parcel.parcel_id}" in project '
                f'"{parcel.project.project_name}". '
                f'Assessed amount: ₹{compensation.assessed_amount}.'
            )
        )

        return redirect('compensation_list')

    profile = request.user.officer_profile

    if profile.role in ['ADMIN', 'CENTRAL']:

        parcels = LandParcel.objects.all()

    elif profile.role == 'STATE':

        parcels = LandParcel.objects.filter(
            project__state__iexact=profile.state
        )

    elif profile.role == 'DISTRICT':

        parcels = LandParcel.objects.filter(
            project__state__iexact=profile.state,
            project__district__iexact=profile.district
        )

    else:

        parcels = LandParcel.objects.none()

    parcels = parcels.select_related(
        'project'
    ).order_by(
        'project__project_name',
        'parcel_id'
    )

    return render(
        request,
        'land/create_compensation.html',
        {
            'parcels': parcels,
        }
    )

@login_required
def rr_list(request):

    profile = getattr(request.user, 'officer_profile', None)

    if not profile:
        messages.error(
            request,
            'Officer profile not found.'
        )
        return redirect('home')

    rr_cases = RRCase.objects.all()

    if profile.role in ['ADMIN', 'CENTRAL']:

        pass

    elif profile.role == 'STATE':

        rr_cases = rr_cases.filter(
            project__state__iexact=profile.state
        )

    elif profile.role == 'DISTRICT':

        rr_cases = rr_cases.filter(
            project__state__iexact=profile.state,
            project__district__iexact=profile.district
        )

    else:

        rr_cases = rr_cases.none()

    rr_cases = rr_cases.order_by('-created_at')

    return render(
        request,
        'land/rr.html',
        {
            'rr_cases': rr_cases,
        }
    )

@jurisdiction_required
@role_required('ADMIN', 'CENTRAL', 'STATE', 'DISTRICT')
def create_rr(request):

    if request.method == 'POST':

        project_id = request.POST.get('project')
        family_id = request.POST.get('family_id')
        family_name = request.POST.get('family_name')
        displaced = request.POST.get('displaced') == 'on'
        rehabilitation_status = request.POST.get(
            'rehabilitation_status'
        )
        assistance_amount = request.POST.get(
            'assistance_amount'
        )
        remarks = request.POST.get('remarks')

        project = get_object_or_404(
            Project,
            id=project_id
        )
        allowed, message = check_project_jurisdiction(request, project)

        if not allowed:
            messages.error(request, message)
            return redirect('rr_list')

        rr_case = RRCase.objects.create(
            project=project,
            family_id=family_id,
            family_name=family_name,
            displaced=displaced,
            rehabilitation_status=rehabilitation_status,
            assistance_amount=assistance_amount or 0,
            remarks=remarks
        )

        log_audit(
            user=request.user,
            action='CREATE',
            instance=rr_case,
            description=(
                f'Created R&R case for family '
                f'"{rr_case.family_id}" '
                f'("{rr_case.family_name}") in project '
                f'"{project.project_name}".'
            )
        )

        return redirect('rr_list')

    profile = request.user.officer_profile

    if profile.role in ['ADMIN', 'CENTRAL']:

        projects = Project.objects.all()

    elif profile.role == 'STATE':

        projects = Project.objects.filter(
            state__iexact=profile.state
        )

    elif profile.role == 'DISTRICT':

        projects = Project.objects.filter(
            state__iexact=profile.state,
            district__iexact=profile.district
        )

    else:

        projects = Project.objects.none()

    projects = projects.order_by(
        'project_name'
    )

    return render(
        request,
        'land/create_rr.html',
        {
            'projects': projects
        }
    )


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
        return JsonResponse(
            {'error': 'POST request required'},
            status=405
        )

    token = request.POST.get('access_token')

    if not token:
        return JsonResponse(
            {'error': 'Access token missing'},
            status=400
        )

    try:
        supabase_url = os.getenv('SUPABASE_URL')

        if not supabase_url:
            return JsonResponse(
                {'error': 'Supabase configuration missing'},
                status=500
            )

        jwks_url = (
            f'{supabase_url}/auth/v1/.well-known/jwks.json'
        )

        # Get the signing key corresponding to this JWT.
        jwks_client = PyJWKClient(jwks_url)
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        # Verify signature + expiration + issuer.
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=['ES256'],
            audience='authenticated',
            issuer=f'{supabase_url}/auth/v1',
            leeway=60
        )

        email = payload.get('email')

        if not email:
            return JsonResponse(
                {'error': 'Email missing from token'},
                status=401
            )

        user = User.objects.filter(
            email__iexact=email
        ).first()

        if not user:
            return JsonResponse(
                {
                    'error': (
                        'Your account has not been provisioned '
                        'as an NLAMS officer.'
                    )
                },
                status=403
            )

        profile = getattr(user, 'officer_profile', None)

        if not profile:
            return JsonResponse(
                {
                    'error': (
                        'Your account has not been assigned '
                        'an NLAMS officer profile.'
                    )
                },
                status=403
            )

        login(request, user)

        return JsonResponse({
            'success': True,
            'role': profile.role,
            'department': profile.department,
            'state': profile.state,
            'district': profile.district,
        })

    except jwt.ExpiredSignatureError:
        return JsonResponse(
            {'error': 'Authentication token has expired'},
            status=401
        )

    except jwt.InvalidIssuerError:
        return JsonResponse(
            {'error': 'Invalid token issuer'},
            status=401
        )

    except jwt.InvalidAudienceError:
        return JsonResponse(
            {'error': 'Invalid token audience'},
            status=401
        )

    except jwt.InvalidTokenError:
        return JsonResponse(
            {'error': 'Invalid authentication token'},
            status=401
        )

    except Exception:
        return JsonResponse(
            {'error': 'Authentication verification failed'},
            status=401
        )
@login_required
@role_required('ADMIN')
def officer_management(request):

    if request.method == 'POST':

        email = request.POST.get('email', '').strip()
        role = request.POST.get('role')
        department = request.POST.get('department', '').strip()
        state = request.POST.get('state', '').strip()
        district = request.POST.get('district', '').strip()

        if not email or not role:
            messages.error(
                request,
                'Email and role are required.'
            )
            return redirect('officer_management')

        user, created = User.objects.get_or_create(
            username=email,
            defaults={
                'email': email
            }
        )

        profile, profile_created = OfficerProfile.objects.update_or_create(
            user=user,
            defaults={
                'role': role,
                'department': department,
                'state': state,
                'district': district,
            }
        )

        messages.success(
            request,
            f'Officer profile for {email} has been provisioned.'
        )

        return redirect('officer_management')

    officers = OfficerProfile.objects.select_related(
        'user'
    ).order_by(
        'user__email'
    )

    return render(
        request,
        'land/officer_management.html',
        {
            'officers': officers,
        }
    )

@jurisdiction_required
@role_required('ADMIN', 'CENTRAL', 'STATE', 'DISTRICT')
def site_photos(request, project_id):

    project = get_object_or_404(
        Project,
        id=project_id
    )

    if request.method == 'POST':

        photo = request.FILES.get('photo')
        caption = request.POST.get('caption', '')
        category = request.POST.get('category', 'SITE')
        parcel_id = request.POST.get('parcel')

        parcel = None

        if parcel_id:
            parcel = LandParcel.objects.filter(
                id=parcel_id,
                project=project
            ).first()

        if photo:
            site_photo = SitePhoto.objects.create(
                project=project,
                parcel=parcel,
                photo=photo,
                caption=caption,
                category=category,
                uploaded_by=request.user
            )

            parcel_label = (
                parcel.parcel_id
                if parcel
                else 'Project Level'
            )

            log_audit(
                user=request.user,
                action='UPLOAD',
                instance=site_photo,
                description=(
                    f'Uploaded site photo for project '
                    f'"{project.project_name}", '
                    f'parcel "{parcel_label}", '
                    f'category "{category}".'
                )
            )

        return redirect(
            'site_photos',
            project_id=project.id
        )

    photos = SitePhoto.objects.filter(
        project=project
    ).select_related(
        'parcel',
        'uploaded_by'
    ).order_by(
        '-uploaded_at'
    )

    parcels = LandParcel.objects.filter(
        project=project
    )

    return render(
        request,
        'land/site_photos.html',
        {
            'project': project,
            'photos': photos,
            'parcels': parcels,
        }
    )
@jurisdiction_required
@role_required('ADMIN', 'CENTRAL', 'STATE', 'DISTRICT')
def delete_site_photo(request, photo_id):

    photo = get_object_or_404(
        SitePhoto,
        id=photo_id
    )

    project_id = photo.project.id

    if request.method == 'POST':

        parcel_id = (
            photo.parcel.parcel_id
            if photo.parcel
            else 'Project Level'
        )

        log_audit(
            user=request.user,
            action='DELETE',
            instance=photo,
            description=(
                f'Deleted site photo from '
                f'project "{photo.project.project_name}", '
                f'parcel "{parcel_id}".'
            )
        )

        photo.delete()

    return redirect(
        'site_photos',
        project_id=project_id
    )
@login_required
def audit_logs(request):

    logs = AuditLog.objects.select_related(
        'user'
    ).order_by(
        '-created_at'
    )

    return render(
        request,
        'land/audit_logs.html',
        {
            'logs': logs,
        }
    )
def logout_user(request):
    logout(request)
    return redirect('login_page')
