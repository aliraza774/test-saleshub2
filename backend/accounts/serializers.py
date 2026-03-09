from django.contrib.auth import authenticate
from rest_framework import serializers

from .models import User


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("id", "name", "email", "password", "role")
        read_only_fields = ("id", "role")

    def create(self, validated_data):
        role = self.context.get("role")
        if role not in (User.Role.CUSTOMER, User.Role.COMPANY):
            raise serializers.ValidationError("Invalid role for signup.")
        password = validated_data.pop("password")
        user = User.objects.create_user(role=role, password=password, **validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        user = authenticate(request=self.context.get("request"), email=email, password=password)
        if not user:
            raise serializers.ValidationError("Invalid email or password.")
        if not user.is_active:
            raise serializers.ValidationError("User account is inactive.")

        attrs["user"] = user
        return attrs


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("age", "gender")

    def validate_age(self, value):
        if value is not None and (value < 1 or value > 150):
            raise serializers.ValidationError("Please enter a valid age.")
        return value

