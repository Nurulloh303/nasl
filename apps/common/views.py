from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.ai_requests.prompt_data import MODULE_DEFINITIONS

class ModuleMetaView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"modules": MODULE_DEFINITIONS})
