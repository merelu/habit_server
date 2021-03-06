from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate, login
from account.models import User

from account.serializers import RegisterUserSerializer, UserSerializer
from rest_framework.permissions import IsAdminUser, AllowAny, IsAuthenticated
from account.permissions import IsSelf

from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action

from django.conf import settings
import jwt


class UserViewSet(ModelViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()

    def get_user(self, pk):
        try:
            user = User.objects.get(pk=pk)
            return user
        except User.DoesNotExist:
            return None

    def get_permissions(self):
        if self.action == "list":
            permission_classes = [IsAdminUser]
        elif (
            self.action == "create"
            or self.action == "retrieve"
            or self.action == "login"
        ):
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsSelf, IsAuthenticated]
        return [permission() for permission in permission_classes]

    def create(self, request):
        serializer = RegisterUserSerializer(data=request.data)
        if serializer.is_valid():
            new_user = serializer.create()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        print('this method is not allowed')
        return Response({'message': 'this method is not allowed'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['POST'])
    def withdraw(self, request):
        user = request.user
        self.perform_destroy(user)
        return Response({'message': '회원탈퇴가 완료되었습니다'}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['POST'])
    def login(self, request):
        email = request.data.get('email', None)
        password = request.data.get('password', None)

        if not email or not password:
            return Response({'message': 'email, 비밀번호를 입혁해주세요'}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(email=email, password=password)
        if user is not None:
            encoded_jwt = jwt.encode(
                {"id": user.pk}, settings.SECRET_KEY, algorithm="HS256"
            )
            return Response(data={'token': encoded_jwt, 'user': UserSerializer(user).data})
        else:
            return Response({'message': '로그인에 실패했습니다.'}, status=status.HTTP_400_BAD_REQUEST)
