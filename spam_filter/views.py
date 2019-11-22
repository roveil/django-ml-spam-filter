import logging
from rest_framework.views import APIView

from django_ml_spam_filter.responses import APIResponse
from spam_filter.learning_models import NN
from spam_filter.models import LearningMessage
from spam_filter.serializers import CheckContentSerializer, LearnContentSerializer
from spam_filter.tasks import process_learning_message

logger = logging.getLogger('default')


class CheckHandler(APIView):
    signed_field = 'content'

    def post(self, request):
        serializer = CheckContentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        spam = NN.check_message_for_spam(serializer.validated_data['content'])
        LearningMessage.objects.create(message=serializer.validated_data['content'], spam=spam)

        return APIResponse({'spam': spam})


class LearnHandler(APIView):
    signed_field = 'learning_content'

    def post(self, request):
        serializer = LearnContentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        messages = [LearningMessage(message=item['content'], spam=item['spam']) for item in
                    serializer.validated_data['learning_content']]

        LearningMessage.objects.bulk_create(messages)

        if serializer.validated_data['immediately']:
            process_learning_message.delay()

        return APIResponse()
