from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from .models import User

class CustomUserCreateForm(UserCreationForm):
    password1 = forms.CharField(label='비밀번호' , widget=forms.PasswordInput())
    password2 = forms.CharField(label="비밀번호 확인",
                                widget=forms.PasswordInput(),
                                help_text="비밀번호 확인을 위해 이전과 동일한 비밀번호를 입력하세요.")
    
    class Meta:
        model = User
        fields =['username','password1','password2','name','email','phone']