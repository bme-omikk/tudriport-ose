from os import environ
import jinja2
from django.conf import settings
from os.path import split, join
from api.external import get_author_points, get_publications_points
from django.utils.translation import gettext as _
from scoring.riport_gpk_phd import thesis_related_to_value, share_from_url_supervisors
import datetime
def render_with_jinja(tpl_path, context):
    tpl_path = join(settings.SITE_ROOT, tpl_path)
    path, filename = split(tpl_path)
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(path or './'),
        extensions=['jinja2.ext.i18n']
    )
    template = env.get_template(filename)
    gmt1 = datetime.timezone(datetime.timedelta(hours=1), "GMT+1")
    template.globals.update({'_': _, 'now': datetime.datetime.now(gmt1), 'thesis_related_to_value': thesis_related_to_value, 'share_from_url_supervisors': share_from_url_supervisors})
    return template.render(context)

def get_jinja_context(mode, author, mtmt_id, year, dbdatetime):
    return {
        'author': author,
        'points': get_author_points(mode, mtmt_id, year, dbdatetime),
        'extra': {'mtmt_url': "https://m2.mtmt.hu/api/publication/?&format=html&cite_type=2&ty_on=1&st_on=1&com_on=1&la_on=1&sort=publishedYear,desc&sort=firstAuthor,asc&size=100&cond=mtid;in;"},
    }

def get_publications_jinja_context(mode, publisheds, year=None):
    return {
        'author': 'Több szerző',
        'points': get_publications_points(mode, publisheds, year),
        'extra': {'mtmt_url': "https://m2.mtmt.hu/api/publication/?&format=html&cite_type=2&ty_on=1&st_on=1&com_on=1&la_on=1&sort=publishedYear,desc&sort=firstAuthor,asc&size=100&cond=mtid;in;"},
    }
