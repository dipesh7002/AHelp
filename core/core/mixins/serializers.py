from rest_framework.serializers import ModelSerializer

class CommonSerializer(ModelSerializer):
    class Meta:
        exclude = ["id", "created_on", "modified_on"]
        abstract =  True