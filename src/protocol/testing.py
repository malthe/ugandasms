from router import testing
from router import orm

class FunctionalTestCase(testing.FunctionalTestCase):
    def setUp(self):
        super(FunctionalTestCase, self).setUp()

        # setup admin user
        from . import models
        admin = models.User(
            id=0,
            name=u"Administrator",
            number="256000000000",
            mask=models.GROUPS['ADM'].mask)

        session = orm.Session()
        session.add(admin)
        session.commit()
