def get_user_organization(request):
    """
    Obtiene la organizacion asociada al usuario autenticado a traves de su UserProfile.
    Reglas de seguridad (Clase 5):
    - Superusuario: devuelve None (conserva acceso global a todas las organizaciones).
    - Usuario anonimo o no autenticado: devuelve None.
    - Usuario staff con UserProfile y organizacion: devuelve la Organization correspondiente.
    - Usuario staff sin perfil o sin organizacion: devuelve None para fail-safe (nunca debe ampliar acceso).
    """
    if not request or not getattr(request, "user", None):
        return None

    user = request.user
    if not user.is_authenticated:
        return None

    if user.is_superuser:
        return None

    profile = getattr(user, "profile", None)
    if not profile or not profile.organization_id:
        return None

    return profile.organization
