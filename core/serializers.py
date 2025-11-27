from rest_framework import serializers

class VoteSerializer(serializers.Serializer):
    # O JavaScript vai mandar: { "slot_ids": [1, 5, 8] }
    slot_ids = serializers.ListField(
        child=serializers.IntegerField()
    )