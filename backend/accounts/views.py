"""HTTP-точки входу для акаунтів (files/SPEC.md §3.5)."""

from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated

from accounts.models import User
from accounts.serializers import RegisterSerializer, UserSerializer


class RegisterView(generics.CreateAPIView):
    """`POST /api/auth/register/` — створення акаунта. Токени видає окремий ендпоінт."""

    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    queryset = User.objects.all()


class MeView(generics.RetrieveAPIView):
    """`GET /api/auth/me/` — хто зараз за токеном; звідси клієнт бере ім'я та e-mail (A1)."""

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self) -> User:
        return self.request.user
