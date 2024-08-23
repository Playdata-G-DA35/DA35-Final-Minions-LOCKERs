from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()

class Faces(models.Model):
    face_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    face_data = models.BinaryField()  # 얼굴 임베딩 데이터를 바이너리 필드로 저장
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)      # 업데이트 시 자동으로 현재 시간 저장

    class Meta:
        managed = True  # 이 옵션은 Django가 이 테이블을 직접 관리하지 않도록 설정 (이미 존재하는 테이블에 대해 사용)
        db_table = 'faces'  # 데이터베이스에서 테이블 이름이 'Faces'임을 명시

    def __str__(self):
        return f"{self.user.username}'s face data"
    
    def get_face_data(self):
        # face_data를 반환하는 메서드 추가
        return self.face_data

