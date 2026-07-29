from .riport_gtk_phd import RIPORT as GTK_PHD_BASE

from common.constants import TUDRIPORT_VIEW_TYPE_LIST, TUDRIPORT_VIEW_TYPE_DETAIL, TUDRIPORT_VIEW_TYPE_ADHOC

class RIPORT(GTK_PHD_BASE):
    """GTK témavezteői ellenőrzés (PhD pontozó, 5 éves teljesítményre)"""
    def __init__(self):
        GTK_PHD_BASE.__init__(self, p_publicationPointTreshold=20, p_max3ScoreCap=5.0, p_constraintMultiplier=1, p_ignoreSupervisor=False)

    @classmethod
    def check_params(cls, view, params):
        """check the content of params dictionary for scoring view given in view. vies should take one of list/detail/adhoc
        Return the list of error messages or an empty list if no errors found.
        """
        msg = GTK_PHD_BASE.check_params(view, params)

        if view in [TUDRIPORT_VIEW_TYPE_LIST, TUDRIPORT_VIEW_TYPE_DETAIL] and params.get('year') is None:
            msg.append('Nem adta meg az év értékelési paramétert, kérjük, írja be vagy válassza ki az évet (az év megadása az 5 éves értékelési periódus záróévét jelöli ki).')

        return msg

    def filter_for_year_publisheds(self, year, publisheds):
        if year is not None:
            publisheds = publisheds.filter(pubdate__range=(int(year)-4, int(year)))
        return publisheds
