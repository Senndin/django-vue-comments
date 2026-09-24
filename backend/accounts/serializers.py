"""Серіалізатори користувачів: реєстрація і профіль (T10, A1)."""

from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from accounts.models import User


class RegisterSerializer(serializers.ModelSerializer):
    """Реєстрація: ім'я за тим самим правилом, що й у коментарях (R5, A7)."""

    password = serializers.CharField(
        write_only=True,
        # Перевірки Django: довжина, не лише цифри, не зі списку найпоширеніших.
        validators=[validate_password],
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = ("id", "username", "email", "password")

    def create(self, validated_data: dict) -> User:
        # `create_user`, а не `create`: інакше пароль ляже в базу відкритим текстом.
        return User.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    """Профіль поточного користувача: рівно те, що потрібно формі коментаря (A1)."""

    class Meta:
        model = User
        fields = ("id", "username", "email")
        read_only_fields = fields
