from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def role_required(*allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):

            profile = getattr(request.user, 'officer_profile', None)

            if not profile:
                messages.error(
                    request,
                    'Officer profile not found.'
                )
                return redirect('home')

            if profile.role not in allowed_roles:
                messages.error(
                    request,
                    'You do not have permission to perform this action.'
                )
                return redirect('home')

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


def jurisdiction_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):

        profile = getattr(request.user, 'officer_profile', None)

        if not profile:
            messages.error(
                request,
                'Officer profile not found.'
            )
            return redirect('home')

        if profile.role in ['ADMIN', 'CENTRAL']:
            return view_func(request, *args, **kwargs)

        project_id = kwargs.get('project_id')

        if not project_id:
            messages.error(
                request,
                'Project information is required.'
            )
            return redirect('home')

        from .models import Project

        project = Project.objects.filter(id=project_id).first()

        if not project:
            messages.error(
                request,
                'Project not found.'
            )
            return redirect('home')

        if profile.role == 'STATE':
            if profile.state.strip().lower() != project.state.strip().lower():
                messages.error(
                    request,
                    'You do not have access to this state.'
                )
                return redirect('home')

        elif profile.role == 'DISTRICT':
            if (
                profile.state.strip().lower() != project.state.strip().lower()
                or
                profile.district.strip().lower() != project.district.strip().lower()
            ):
                messages.error(
                    request,
                    'You do not have access to this district.'
                )
                return redirect('home')

        return view_func(request, *args, **kwargs)

    return wrapper
def check_project_jurisdiction(request, project):
    profile = getattr(request.user, 'officer_profile', None)

    if not profile:
        return False, 'Officer profile not found.'

    if profile.role in ['ADMIN', 'CENTRAL']:
        return True, ''

    if profile.role == 'STATE':
        if profile.state.strip().lower() != project.state.strip().lower():
            return False, 'You do not have access to this state.'

    elif profile.role == 'DISTRICT':
        if (
            profile.state.strip().lower() != project.state.strip().lower()
            or
            profile.district.strip().lower() != project.district.strip().lower()
        ):
            return False, 'You do not have access to this district.'

    return True, ''