from django.urls import path
from . import views

app_name = 'field'

urlpatterns = [
    path('recognize/', views.recognize_face, name='recognize_face'),  # URL을 recognize로 변경
]
