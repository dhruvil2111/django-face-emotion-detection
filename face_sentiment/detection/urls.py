from django.urls import path
from .views import video_feed, index, get_emotion_data

urlpatterns = [
    path("", index, name="index"),
    path("video_feed/", video_feed, name="video_feed"),
    path("emotion_data/", get_emotion_data, name="emotion_data"),
]
