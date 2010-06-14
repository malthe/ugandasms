import csv
import sys
import pyproj
import traceback

from django.core.management.base import BaseCommand
from location.models import LocationKind
from location.models import Area
from location.models import Facility

wgs84 = pyproj.Proj(proj='latlong', datum='WGS84')
utm33 = pyproj.Proj(proj='utm', zone='33')

class Command(BaseCommand):
    args = 'path'
    help = 'Imports the specified .cvs file'

    def handle(self, path, **options):
        areas = Area.objects.count()
        facilities = Facility.objects.count()
        print "%d existing areas." % areas
        print "%d existing facilities." % facilities

        reader = csv.reader(open(path), delimiter=',', quotechar='"')
        parent = None

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
        for index, line in enumerate(reader):
            line.extend(
                [""]*(21-len(line)))
            try:
                code, name, level, itp_otc_status, distribution_day, iycf, x, y, parent_composite, district, county, sub_county, parish, village, sub_village, household, house_holds, population, needed_vhts, trained_vhts, vhts_to_be_trained = line
            except Exception, exc:
                print traceback.format_exc(exc)
                continue

            if x and y:
                transformed = pyproj.transform(utm33, wgs84, float(x), float(y))
                longitude, latitude = map(str, transformed)
            else:
                longitude, latitude = None, None

            # create new facility if required
            try:
                facility = Facility.objects.get(code=code)
            except Facility.DoesNotExist:
                if level:
                    level = level.replace(' ', '')
                    try:
                        slug = level.lower()
                        kind = LocationKind.objects.get(slug=slug)
                    except LocationKind.DoesNotExist:
                        print "%03d Skipping row "
                        "(unable to look up location kind '%s')" % (
                            index+2, level)
                    else:
                        if parent_composite:
                            n, l = parent_composite.rsplit(' ', 1)
                            try:
                                parent = Facility.objects.get(
                                    name=n, kind__slug=l.lower())
                            except Facility.DoesNotExist:
                                print "%03d Skipping row (unable to find " \
                                      "reporting facility with name '%s')." % (
                                    index+2, n)
                                continue

                            create = parent.add_child
                        else:
                            create = Facility.add_root

                        facility = create(
                            name=name,
                            kind=kind,
                            code=code,
                            longitude=longitude,
                            latitude=latitude,
                            )

                        # explicit reload of non-trivial parent
                        if parent is not None:
                            parent = Facility.objects.get(pk=parent.pk)

            # update locations
            locations = ((district, _k_district),
                         (county, _k_county),
                         (sub_county, _k_sub_county),
                         (parish, _k_parish),
                         (village, _k_village),
                         (sub_village, _k_sub_village))

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
