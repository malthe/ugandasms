import messages

from router.parser import Parser

patterns = (
    (r'^$',
     messages.Empty),
    (r'^\+reg(ister)?\s+(?P<name>[^,]+)\s*(,\s*(?P<location>.+))?$',
     messages.Registration),
    (r'^\+(?P<role>vht|hc.)\s+(?P<facility>\d+)$',
     messages.HealthWorkerSignup),
    )

parser = Parser(patterns)
