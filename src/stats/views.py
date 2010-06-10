from datetime import datetime
from datetime import timedelta
from itertools import chain

from django.db.models import aggregates
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django import forms

from router.transports import Message

from location.models import Area

from .models import Report
from .models import ReportKind
from .models import ObservationKind
from .models import Observation

transport = Message("web")

def decimal_renderer(value):
    return "%0.f" % value

def timedelta_renderer(value):
    days = int(value)
    if days > 365:
        return "%d years" % (days // 365)
    elif days > 30:
        return "%d months" % (days // 30)
    return "%d days" % days

AGGREGATORS = {
    'avg': aggregates.Avg('value'),
    'sum': aggregates.Sum('value'),
    }

RENDERERS = {
    None: decimal_renderer,
    'timedelta': timedelta_renderer,
    }

TIMEFRAME_CHOICES = (
    (7, "Weekly"),
    (30, "Monthly"),
    (90, "Quarterly"),
    (365, "Yearly"),
    )

class NO_LOCATION:
    name = "-"

class TOP_LOCATION:
    name = "All"
    pk = ""

    @classmethod
    def get_ancestors(self):
        return ()

class StatsForm(forms.Form):
    timeframe = forms.TypedChoiceField(
        choices=TIMEFRAME_CHOICES, coerce=int, initial=7, required=False)

@login_required
def reports(req):
    """Aggregate observations by report and location."""

    form = StatsForm(req.GET)
    days = form.fields['timeframe'].initial
    location = req.GET.get('location')

    if form.is_valid():
        days = form.cleaned_data.get('timeframe') or days

    now = datetime.now()
    gte = now - timedelta(days=days)

    # set up columns
    sort_column, sort_descending = _get_sort_info(
        req, default_sort_column=None, default_sort_descending=True)

    # determine top-level locations
    if location:
        root = Area.objects.get(pk=int(location))
        locations = root.get_children().all()
    else:
        root = TOP_LOCATION
        first_node = Area.get_first_root_node()
        if first_node is None:
            locations = []
        else:
            locations = list(first_node.get_siblings().all())
        locations.append(NO_LOCATION)

    report_kinds = ReportKind.objects.all()
    non_trivial_observation_kinds = set()

    by_location = {}
    for location in locations:
        if location is not NO_LOCATION:
            tree = Area.get_tree(location)

        by_report_kind = by_location.setdefault(location, {})

        # for each report kind and its observation kinds, compute
        # aggregated values
        if location is not NO_LOCATION:
            query = Report.objects.filter(location__in=tree)
        else:
            query = Report.objects.filter(location=None)

        for report_kind in report_kinds:
            by_observation_kind = by_report_kind.setdefault(
                report_kind, {})

            # to-do: this is probably a slow query
            reports = query.filter(
                kind=report_kind,
                source__message__time__gte=gte).all()

            for observation_kind in report_kind.observation_kinds.all():
                observations = Observation.objects.filter(
                    kind=observation_kind, report__in=reports).all()

                if len(observations) == 0:
                    by_observation_kind[observation_kind] = None
                    continue

                non_trivial_observation_kinds.add(observation_kind)

                aggregator = AGGREGATORS[observation_kind.aggregator]
                result = observations.aggregate(aggregator)
                renderer = RENDERERS[observation_kind.renderer]
                aggregate = renderer(result.values()[0])
                by_observation_kind[observation_kind] = aggregate

    if sort_column:
        sort_kind = ObservationKind.objects.get(slug=sort_column)
        location_sort = lambda location: \
                        by_location[location][sort_kind.group][sort_kind]
    else:
        location_sort = None

    # if we're showing more than one report kind, prioritize
    # non-trivial observations; we take the top priority from each
    # report kind and in order of priority fill up to the desired
    # number of observations (columns)
    if len(report_kinds) > 1:
        max_columns = max(8, len(report_kinds))
        prioritized = []

        sorted_non_trivial_kinds = sorted(
            non_trivial_observation_kinds,
            key=lambda kind: kind.priority)

        for report_kind in report_kinds:
            kinds = filter(
                sorted_non_trivial_kinds.__contains__,
                report_kind.observation_kinds.all())

            if len(kinds) == 0:
                continue

            top_priority = kinds[0]
            prioritized.append(top_priority)
            sorted_non_trivial_kinds.remove(top_priority)

        missing = max_columns-len(prioritized)
        prioritized.extend(sorted_non_trivial_kinds[:missing])
        assert len(prioritized) <= max_columns

    # set up columns to map report kinds to observation kinds
    columns = []
    for report_kind in sorted(report_kinds):
        kinds = filter(
            prioritized.__contains__,
            report_kind.observation_kinds.all())

        if len(kinds) == 0:
            continue

        columns.append((report_kind, sorted(kinds)))

    for index, timeframe in TIMEFRAME_CHOICES:
        if days == index:
            break

    observations_by_location = [
        (location, tuple(chain(*(
            [value for kind, value in sorted(by_observation_kind.items())
             if kind in prioritized]
            for (report_kind, by_observation_kind) in sorted(
                by_location[location].items())))))
        for location in sorted(
            locations, key=location_sort, reverse=sort_descending)
        ]

    return render_to_response(
        "statsui/reports.html", {
            'form': form,
            'columns': columns,
            'location': root,
            'observations_by_location': observations_by_location,
            'sort_column': sort_column,
            'sort_descending': sort_descending,
            'timeframe': timeframe,
            },
        RequestContext(req))

def _get_sort_info(request, default_sort_column, default_sort_descending):
    sort_column = default_sort_column
    sort_descending = default_sort_descending
    if "sort_column" in request.GET:
        sort_column = request.GET["sort_column"]
    if "sort_descending" in request.GET:
        if request.GET["sort_descending"].startswith("f"):
            sort_descending = False
        else:
            sort_descending = True
    return (sort_column, sort_descending)
