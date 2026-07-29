from .riport_gtk_ter import RIPORT as GTK_TER_BASE

class RIPORT(GTK_TER_BASE):
    """GTK TÉR (teljesítményértékelés) pontozó. (angol verzió)"""
    def __init__(self):
        GTK_TER_BASE.__init__(self)
