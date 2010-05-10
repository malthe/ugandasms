patterns = (
    (r'^$', 'router.Empty'),
    (r'^\+reg(ister)?\s+(?P<name>[^,]+)\s*(,\s*(?P<location>.+))?$', 'registration.Registration'),
    (r'^\+(?P<role>vht|hc.)\s+(?P<facility>\d+)$', 'health.Signup'),
    )
