from router.testing import FunctionalTestCase

class AggregationTestCase(FunctionalTestCase):
    INSTALLED_APPS = FunctionalTestCase.INSTALLED_APPS + (
        'stats',
        'location',
        )

    def setUp(self):
        super(AggregationTestCase, self).setUp()

        # set up locations
        from location.models import Area
        from location.models import LocationKind

        root_kind, _ = LocationKind.objects.get_or_create(slug="root")
        child_kind, _ = LocationKind.objects.get_or_create(slug="child")
        root = Area.add_root(name="Root", kind=root_kind)
        self.child1 = root.get().add_child(name="1", kind=child_kind)
        self.child2 = root.get().add_child(name="2", kind=child_kind)

        # set up report kinds and observation kinds
        from stats.models import Report
        from stats.models import ReportKind
        from stats.models import Observation
        from stats.models import ObservationKind

        report_kind1, _ = ReportKind.objects.get_or_create(
            slug="1", name="1")
        report_kind2, _ = ReportKind.objects.get_or_create(
            slug="2", name="2")
        report_kind1, _ = ReportKind.objects.get_or_create(
            slug="3", name="3")

        observation_kind11, _ = ObservationKind.objects.get_or_create(
            slug="11", name="1", group=report_kind1)
        observation_kind12, _ = ObservationKind.objects.get_or_create(
            slug="12", name="2", group=report_kind1)
        observation_kind21, _ = ObservationKind.objects.get_or_create(
            slug="21", name="1", group=report_kind2)
        observation_kind22, _ = ObservationKind.objects.get_or_create(
            slug="22", name="2", group=report_kind2)

    def test_aggregates(self):
        pass
