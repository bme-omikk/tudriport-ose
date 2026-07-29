from rest_framework.pagination import PageNumberPagination


class ExtendedPageNumberPagination(PageNumberPagination):
    def get_paginated_response(self, data):
        response = super().get_paginated_response(data)
        response.data['page_size'] = self.page_size
        return response
