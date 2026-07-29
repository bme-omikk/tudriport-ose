from .riport_gtk_phd import RIPORT as GTK_PHD_BASE

class RIPORT(GTK_PHD_BASE):
    """GTK habilitációs pontozó"""
    def __init__(self):
        GTK_PHD_BASE.__init__(self, p_publicationPointTreshold=100, p_max3ScoreCap=25.0, p_constraintMultiplier=5, p_ignoreSupervisor=False)
