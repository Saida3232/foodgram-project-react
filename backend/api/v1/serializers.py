import base64
import datetime as dt
from django.contrib.auth import get_user_model
import webcolors
from django.core.files.base import ContentFile
from djoser.serializers import UserCreateSerializer
from rest_framework import serializers
from user.models import Follow
from foodgram.models import Recipe, Tag, Ingredient, Favorite
from rest_framework.validators import UniqueTogetherValidator


User = get_user_model()





class Hex2NameColor(serializers.Field):
    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        try:
            data = webcolors.hex_to_name(data)
        except ValueError:
            raise serializers.ValidationError('Для этого цвета нет имени')
        return data


class TagSerializer(serializers.ModelSerializer):
    color = Hex2NameColor()
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerialiazer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = "__all__"


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)




class FollowSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        read_only=True, slug_field='username',
        default=serializers.CurrentUserDefault())
    following = serializers.SlugRelatedField(
        slug_field='username', queryset=User.objects.all())

    class Meta:
        model = Follow
        fields = ('user', 'following','created')
        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=['user', 'following'],
                message='Нельзя дважды подписаться на одного человека.'
            )
        ]

    def validate_following(self, data):
        request = self.context.get('request')
        following = data
        if request.user == following:
            raise serializers.ValidationError(
                "Низя на себя подиписываться."
            )
        return data


class CustomUserSerializer(UserCreateSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta():
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'is_subscribed')
        
    def get_is_subscribes(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous():
            return False
        else:
            return Follow.objects.filter(user=user,author=obj.id).exists()

class CreateUserSerializer(UserCreateSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'username',
                  'first_name', 'last_name',
                  'password')




class ReceipeCreareSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username',
        default=serializers.CurrentUserDefault()
    )
    tag = TagSerializer(many=True)
    image = Base64ImageField(required=False, allow_null=True)
    ingredients = IngredientSerialiazer(many=True)
    #cooking_duration = serializers.DurationField(min_value=dt.timedelta(minutes=1))
    
    class Meta:
        model = Recipe
        fields = ('__all__')
    

    def create(self, validated_data):
        if 'ingredients' and 'tag' not in self.initial_data:
            recipe = Recipe.objects.create(**validated_data)
            return recipe
        if 



class ReceipeAllSerializer(serializers.ModelSerializer):
    author = CustomUserSerializer(read_only=True)
    tags = TagSerializer(many=True)
    image = Base64ImageField(required=False, allow_null=True)
    

    class Meta:
        model = Recipe
        fields = ('__all__')
        read_only_fields = ('owner',)


class FavoriteSerialiser(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ('id', 'receipes__name', 'receipes__image', 'receipes__cooking_time')