from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class RegisterView(APIView):
    def post(self, request):
        return Response({"message": "User registered successfully."}, status=status.HTTP_201_CREATED)

class LoginView(APIView):
    def post(self, request):
        return Response({"token": "dummy-jwt-token"}, status=status.HTTP_200_OK)
