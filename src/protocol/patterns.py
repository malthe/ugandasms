import messages

from router.parser import Parser

patterns = (
    (r'^$', messages.Empty),
    (r'^\+reg(ister)?\s+(?P<name>[^,]+)\s*(,\s*(?P<location>.+))?$', messages.Register),
    (r'^\+approve\s+(?P<id>\d+)\s+(?P<group>\w+)$', messages.Approve),
    )

parser = Parser(patterns)
