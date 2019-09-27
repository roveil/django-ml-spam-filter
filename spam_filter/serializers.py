from rest_framework import serializers


class CheckContentSerializer(serializers.Serializer):
    content = serializers.CharField()


class LearnEntrySerializer(serializers.Serializer):
    content = serializers.CharField()
    spam = serializers.BooleanField()


class LearnContentSerializer(serializers.Serializer):
    learning_content = serializers.ListField(child=LearnEntrySerializer(), min_length=1, max_length=1000)
    immediately = serializers.BooleanField(required=False, default=False)
