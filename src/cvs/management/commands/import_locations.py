import pyproj
import csv
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
        Area.objects.all().delete()
        Facility.objects.all().delete()

        reader = csv.reader(open(path), delimiter=',', quotechar='"')

        parent = None

        # location roots
        country = Area.add_root(
            name="Uganda", kind=LocationKind.objects.get(name='Country'))
        facility = Facility.add_root(
            name="Amuru", code="71", kind=LocationKind.objects.get(name='DHO'))

        _k_district = LocationKind.objects.get(name="District")
        _k_county = LocationKind.objects.get(name="County")
        _k_sub_county = LocationKind.objects.get(name="Sub-county")
        _k_parish = LocationKind.objects.get(name="Parish")
        _k_village = LocationKind.objects.get(name="Village")
        _k_sub_village = LocationKind.objects.get(name="Sub-village")

        reader.next()
        for index, line in enumerate(reader):
            line.extend(
                [""]*(21-len(line)))
            try:
                code, name, level, itp_otc_status, distribution_day, iycf, x, y, parent_composite, district, county, sub_county, parish, village, sub_village, household, house_holds, population, needed_vhts, trained_vhts, vhts_to_be_trained = line
            except Exception, exc:
                print traceback.format_exc(exc)
                continue

            # prefix with the amuru district code
            code = "71" + code

            if x and y:
                transformed = pyproj.transform(utm33, wgs84, float(x), float(y))
                longitude, latitude = map(str, transformed)
            else:
                longitude, latitude = None, None

            # create new facility if required
            if level:
                level = level.replace(' ', '')
                try:
                    kind = LocationKind.objects.get(name=level)
                except LocationKind.DoesNotExist:
                    print "%03d Skipping row (unable to look up location kind '%s')" % (
                        index+2, level)
                n, l = parent_composite.rsplit(' ', 1)
                try:
                    parent = Facility.objects.get(name=n, kind__name=l)
                except Facility.DoesNotExist:
                    print "%03d Skipping row (unable to find " \
                          "reporting facility with name '%s')." % (index+2, n)
                    continue

                facility = parent.add_child(
                    name=name,
                    kind=kind,
                    code=code,
                    longitude=longitude,
                    latitude=latitude,
                    )

                # explicit reload
                parent = Facility.objects.get(pk=parent.pk)

            # update locations
            locations = ((district, _k_district),
                         (county, _k_county),
                         (sub_county, _k_sub_county),
                         (parish, _k_parish),
                         (village, _k_village),
                         (sub_village, _k_sub_village))

            parent = country
            for placename, kind in locations:
                kwargs = dict(name=placename, kind=kind)
                try:
                    inst = Area.objects.get(**kwargs)
                except Area.DoesNotExist:
                    inst = parent.add_child(report_to=facility, **kwargs)

                parent = Area.objects.get(pk=inst.pk)
