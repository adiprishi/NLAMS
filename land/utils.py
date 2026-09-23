from .models import AuditLog


def log_audit(
    user,
    action,
    instance,
    description
):
    AuditLog.objects.create(
        user=user,
        action=action,
        model_name=instance.__class__.__name__,
        object_id=str(instance.pk),
        description=description
    )