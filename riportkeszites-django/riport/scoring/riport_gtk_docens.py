from .riport_gtk_phd import RIPORT as GTK_PHD_BASE

class RIPORT(GTK_PHD_BASE):
    """GTK docensi pontozó"""
    def __init__(self):
        GTK_PHD_BASE.__init__(self, p_publicationPointTreshold=60, p_max3ScoreCap=15.0, p_constraintMultiplier=3, p_ignoreSupervisor=False)
