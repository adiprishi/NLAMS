from django.shortcuts import render, redirect  # type: ignore[reportMissingModuleSource]
from .models import Project, LandParcel, Compensation, RRCase, Possession
from django.db.models import Sum

def home(request):

    total_projects = Project.objects.count()

    total_land = LandParcel.objects.aggregate(
        total=Sum('area')
    )['total'] or 0

    total_compensation = Compensation.objects.aggregate(
        total=Sum('paid_amount')
    )['total'] or 0

    recent_projects = Project.objects.all().order_by('-created_at')[:5]

    return render(request, 'land/dashboard.html', {
        'total_projects': total_projects,
        'total_land': total_land,
        'total_compensation': total_compensation,
        'recent_projects': recent_projects,
    })


def projects(request):
    project_list = Project.objects.all().order_by('-created_at')

    return render(
        request,
        'land/projects.html',
        {'projects': project_list}
    )


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

def project_detail(request, project_id):

    project = Project.objects.get(id=project_id)

    return render(
        request,
        'land/project_detail.html',
        {'project': project}
    )
def update_status(request, project_id):

    project = Project.objects.get(id=project_id)

    if request.method == 'POST':

        new_status = request.POST.get('status')

        project.status = new_status
        project.save()

    return redirect('project_detail', project_id=project.id)
def land_map(request):
    parcels = LandParcel.objects.all()
    return render(request, 'land/land_map.html', {'parcels': parcels})
def land_parcels(request):
    parcels = LandParcel.objects.all().order_by('-created_at')
    return render(request, 'land/land_parcels.html', {
        'parcels': parcels
    })


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

def compensation_list(request):
    compensations = Compensation.objects.all().order_by('-created_at')

    return render(
        request,
        'land/compensation.html',
        {'compensations': compensations}
    )


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

def rr_list(request):
    rr_cases = RRCase.objects.all().order_by('-created_at')
    return render(request, 'land/rr.html', {
        'rr_cases': rr_cases
    })


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

def possession_list(request):
    possessions = Possession.objects.all().order_by('-created_at')

    return render(request, 'land/possession.html', {
        'possessions': possessions
    })


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

    return render(request, 'land/create_possession.html', {
        'parcels': parcels
    })