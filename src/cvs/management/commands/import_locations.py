import csv
import sys
import pyproj
import traceback
import collections

from django.core.management.base import BaseCommand
from django.template.defaultfilters import slugify as _slugify
from location.models import LocationKind
from location.models import Area
from location.models import Facility

wgs84 = pyproj.Proj(proj='latlong', datum='WGS84')
utm33 = pyproj.Proj(proj='utm', zone='33')

Entry = collections.namedtuple("Entry", "code, name, level, itp_otc_status, distribution_day, iycf, x, y, reports_to, district, county, sub_county, parish, village, sub_village, household, house_holds, population, needed_vhts, trained_vhts, vhts_to_be_trained")

def slugify(string):
    return _slugify(string).replace('-', '')

class Command(BaseCommand):
    args = 'path'
    help = 'Imports the specified .cvs file'

    def handle(self, path, **options):
        areas = Area.objects.count()
        facilities = Facility.objects.count()
        print >> sys.stderr, "%d existing areas." % areas
        print >> sys.stderr, "%d existing facilities." % facilities

        reader = csv.reader(open(path), delimiter=',', quotechar='"')

        _k_country = LocationKind.objects.get(name='Country')
        _k_district = LocationKind.objects.get(slug="district")
        _k_county = LocationKind.objects.get(slug="county")
        _k_sub_county = LocationKind.objects.get(slug="sub_county")
        _k_parish = LocationKind.objects.get(slug="parish")
        _k_village = LocationKind.objects.get(slug="village")
        _k_sub_village = LocationKind.objects.get(slug="sub_village")

        try:
            root = Area.objects.get(name="Uganda", kind=_k_country)
        except Area.DoesNotExist:
            root = Area.add_root(name="Uganda", kind=_k_country)

        reader.next()

        # read all entries
        entries = []
        for line in reader:
            line.extend(
                [""]*(21-len(line)))

            try:
                entry = Entry(*line)
            except Exception, exc:
                print >> sys.stderr, traceback.format_exc(exc)
            else:
                entries.append(entry)

        # read all facilities
        facility_entries = {}
        for entry in entries:
            if entry.name and entry.level:
                name = slugify(entry.name)
                level = slugify(entry.level)
                facility_entries[name, level] = entry

        created = {}
        def get_or_create(entry):
            try:
                return Facility.objects.get(code=entry.code)
            except Facility.DoesNotExist:
                pass

            parent = None

            if entry.reports_to:
                name, level = entry.reports_to.rsplit(' ', 1)

                parent = created.get((name, level))
                if parent is None:
                    try:
                        parent_entry = facility_entries[slugify(name), slugify(level)]
                    except KeyError:
                        raise KeyError("Facility not found: '%s %s'." % (name, level))

                    try:
                        parent = created[name, level] = get_or_create(parent_entry)
                    except RuntimeError:
                        raise RuntimeError(
                            "Recursive definition: %s %s => %s %s." % (
                                entry.code, entry.name,
                                parent_entry.code, parent_entry.name))

                create = parent.get().add_child
            else:
                create = Facility.add_root

            if entry.x and entry.y:
                transformed = pyproj.transform(
                    utm33, wgs84, float(entry.x), float(entry.y))
                longitude, latitude = map(str, transformed)
            else:
                longitude, latitude = None, None

            level = entry.level.replace(' ', '')
            slug = level.lower()
            try:
                kind = LocationKind.objects.get(slug=slug)
            except LocationKind.DoesNotExist:
                raise LocationKind.DoesNotExist(slug)

            facility = create(
                name=entry.name,
                code=entry.code,
                kind=kind,
                longitude=longitude,
                latitude=latitude,
                )

            facility = Facility.objects.get(pk=facility.pk)
            return facility

        facility = None
        for entry in entries:
            # update locations
            locations = ((entry.district, _k_district),
                         (entry.county, _k_county),
                         (entry.sub_county, _k_sub_county),
                         (entry.parish, _k_parish),
                         (entry.village, _k_village),
                         (entry.sub_village, _k_sub_village))

            if entry.code:
                try:
                    facility = get_or_create(entry)
                except RuntimeError, error:
                    print >> sys.stderr, "Warning: %s" % error
                    continue
            elif facility is None:
                continue

            parent = root
            for placename, kind in locations:
                if not placename.strip():
                    break

                kwargs = dict(name=placename, kind=kind)
                try:
                    inst = Area.objects.get(**kwargs)
                except Area.DoesNotExist:
                    inst = parent.add_child(report_to=facility, **kwargs)

                parent = Area.objects.get(pk=inst.pk)

        print >> sys.stderr, "%d areas added." % (
            Area.objects.count() - areas)
        print >> sys.stderr, "%d facilities added." % (
            Facility.objects.count() - facilities)
