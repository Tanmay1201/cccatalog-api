from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from cccatalog.api.search_serializers import ImageSearchResultSerializer, \
    ElasticsearchImageResultSerializer, ValidationErrorSerializer,\
    SearchQueryStringSerializer
from drf_yasg.utils import swagger_auto_schema
import cccatalog.api.search_controller as search_controller


class SearchImages(APIView):
    renderer_classes = (JSONRenderer,)

    @swagger_auto_schema(responses={
                             200: ImageSearchResultSerializer(many=True),
                             400: ValidationErrorSerializer,
                         },
                         query_serializer=SearchQueryStringSerializer)
    def get(self, request, format=None):
        # Parse and validate query parameters
        params = SearchQueryStringSerializer(data=request.query_params)
        if not params.is_valid():
            return Response(
                status=400,
                data={
                    "validation_error": params.errors
                }
            )
        page = params.data['page']
        page_size = params.data['pagesize']
        try:
            search_results = search_controller.search(params,
                                                      index='image',
                                                      page_size=page_size,
                                                      page=page)
        except ValueError:
            return Response(
                status=400,
                data={
                    'validation_error': 'Deep pagination is not allowed.'
                }
            )

        results = [result for result in search_results]
        serialized_results =\
            ElasticsearchImageResultSerializer(results, many=True).data

        # Elasticsearch does not allow deep pagination of ranked queries.
        # Adjust returned page count to reflect this.
        natural_page_count = int(search_results.hits.total/page_size)
        last_allowed_page = int((5000 + page_size / 2) / page_size)
        page_count = min(natural_page_count, last_allowed_page)

        response_data = {
            'result_count': search_results.hits.total,
            'page_count': page_count,
            'results': serialized_results
        }
        serialized_response = ImageSearchResultSerializer(data=response_data)

        return Response(status=200, data=serialized_response.initial_data)


class HealthCheck(APIView):

    def get(self, request, format=None):
        return Response('', status=200)