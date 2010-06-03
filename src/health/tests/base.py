from router.testing import FormTestCase

class Scenario(FormTestCase):
    INSTALLED_APPS = FormTestCase.INSTALLED_APPS + (
        'health',
        'reporter',
        )

    @classmethod
    def _register(cls, **kwargs):
        from reporter.models import Registration
        return cls.handle(Registration, **kwargs)

    def setUp(self):
        super(Scenario, self).setUp()

        form = self._register(name="ann")

        from datetime import datetime
        from ..models import Patient
        from ..models import Report
        from ..models import Case

        from stats.models import ReportKind
        ReportKind(slug="test", name="Test report").save()

        report = Report(slug="test", source=form)
        report.save()

        patient = Patient(
            health_id="bob123",
            name="Bob",
            sex="M",
            birthdate=datetime(1980, 1, 1, 3, 42),
            last_reported_on_by=form.user,
            )
        patient.save()

        case = Case(
            patient=patient,
            report=report,
            tracking_id="TRACK123",
            )

        case.save()
