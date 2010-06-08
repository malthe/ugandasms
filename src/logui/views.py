from django.core.paginator import Paginator
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.db.models import Q

# from rapidsms.webui.utils import paginated

from router.models import Incoming

from django.template import RequestContext

@login_required
def index(req):
    columns = (("time", "Arrival"),
               ("connection", "Identification"),
               ("text", "Message"))

    sort_column, sort_descending = _get_sort_info(
        req, default_sort_column="time", default_sort_descending=True)

    sort_desc_string = "-" if sort_descending else ""
    search_string = req.REQUEST.get("q", "")

    query = Incoming.objects.order_by("%s%s" % (sort_desc_string, sort_column))

    if search_string == "":
        query = query.all()

    else:
        query = query.filter(
            Q(text__icontains=search_string) |
            Q(connection__uri__icontains=search_string))

    messages = Paginator(query, 25)

    return render_to_response("logui/index.html", {
        "columns": columns,
        "messages": messages,
        "sort_column": sort_column,
        "sort_descending": sort_descending,
        "search_string": search_string
        }, RequestContext(req))


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

