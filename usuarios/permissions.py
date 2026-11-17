def es_root(user):
    """Return True only for authenticated superuser accounts."""
    return user.is_authenticated and user.is_superuser
