from rest_framework import fields
from rest_framework.serializers import Serializer, ModelSerializer
from api.serializers.base import UserSerializer
from riport.models.base import ExtendedUser


class ExtAuthorListSerializer(Serializer):
    org = fields.CharField()
    unit = fields.CharField()
    subunit = fields.CharField()
    subsub_unit = fields.CharField(allow_blank=True)
    file_data = fields.CharField()

class MtmtIdSerializer(Serializer):
    mtmt_id = fields.IntegerField(min_value=0)

class MtmtIdListSerializer(Serializer):
    mtmt_id_list = fields.ListField(child=fields.IntegerField(min_value=0))


class ExtendedUserSerializer(ModelSerializer):
    user = UserSerializer()
    orgId = fields.CharField()
    affiliation = fields.CharField()

    class Meta:
        model = ExtendedUser
        fields = ('user', 'orgId', 'affiliation', )
