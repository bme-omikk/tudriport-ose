from django.contrib.auth.models import AnonymousUser, User
from unittest import TestCase
from django.test import RequestFactory, Client
from api.views.template import AuthorListView, AuthorDetailView
class ViewsTestCases(TestCase):  
    def setUp(self):
        self.factory = RequestFactory()
    #Tartalmaz nem 1 hozzájárulású szerzőt
    def test_list_view(self):
        request = RequestFactory().get('/riport/extauthors/gpk/BME/GPK/EGR?year=2017')
        view = AuthorListView()
        view.setup(request, mode='gpk', org='BME', unit='GPK', subunit='EGR', year=2017)

        context = view.get_context_data()   
        self.assertTrue(context['is_aggregation_aware'])
        self.assertAlmostEqual(context['summary']['osszpontszam'], 46.7)
        self.assertAlmostEqual(context['summary']['reszeredmenyek']['CIT-IND,WOS']['reszpont'], 205.0)
        self.assertAlmostEqual(next(obj for obj in context['object_list'] if obj['author'].personname == 'Ván Péter')['author'].weighting, 0.5)
        self.assertAlmostEqual(next(obj for obj in context['object_list'] if obj['author'].personname == 'Ván Péter')['points']['osszpontszam'], 1.0714285714285714)
    
    def test_compare_detail_and_list_view(self):
        request1 = RequestFactory().get('/riport/extauthors/gpk/BME/GPK/EGR?year=2015')
        list_view = AuthorListView()        
        list_view.setup(request1, mode='gpk', org='BME', unit='GPK', subunit='EGR', year=2015)
        list_context = list_view.get_context_data()

        request2 = RequestFactory().get('/riport/detail/gpk/BME/GPK/EGR/2015/')
        detail_view = AuthorDetailView()
        detail_view.setup(request2, mode='gpk', org='BME', unit='GPK', subunit='EGR', year=2015)
        detail_context = detail_view.get_context_data()
        self.assertAlmostEqual(list_context['summary']['osszpontszam'], detail_context['points']['osszpontszam'])