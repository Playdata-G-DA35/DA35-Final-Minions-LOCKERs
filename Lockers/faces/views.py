from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
import cv2
import mediapipe as mp
import numpy as np
from PIL import Image
from facenet_pytorch import InceptionResnetV1
import torch
from torchvision import transforms
import base64
import io
import json
from .models import Faces

# 얼굴 메쉬 및 얼굴 인식 모델 초기화
mp_face_mesh = mp.solutions.face_mesh
transform = transforms.Compose([
    transforms.Resize((160, 160)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
])

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

model = InceptionResnetV1(pretrained=None, classify=False).to(device)
state_dict = torch.load(r"C:\Users\USER\OneDrive\classes\LOCKERs\saved_models\7epoch_colab.pth", map_location=device)
model.load_state_dict(state_dict, strict=False)
model.eval()

def get_embedding_from_image(image):
    image_pil = Image.open(io.BytesIO(base64.b64decode(image.split(',')[1])))
    image_tensor = transform(image_pil).unsqueeze(0).to(device)
    
    with torch.no_grad():
        embedding = model(image_tensor)
    
    return embedding.cpu().numpy().flatten()

@login_required
def register_face(request):
    if request.method == 'POST':
        try:
            body_unicode = request.body.decode('utf-8')
            body_data = json.loads(body_unicode)
            images = body_data.get('images')

            if len(images) != 17:
                return JsonResponse({'success': False, 'message': '이미지 데이터가 17개 모이지 않았습니다.'})
            
            embeddings = []
            for i, image in enumerate(images):
                embedding = get_embedding_from_image(image)
                embeddings.append(embedding)
                print(f"{i+1}/17 각도 이미지 임베딩 추출 완료")

            average_embedding = np.mean(embeddings, axis=0)
            print("평균 임베딩 값 계산 완료:", average_embedding)

            user = request.user
            face_instance = Faces(user=user, face_data=average_embedding)
            face_instance.save()
            print("평균 임베딩 값이 성공적으로 DB에 저장되었습니다.")

            return JsonResponse({'success': True, 'message': '임베딩이 성공적으로 저장되었습니다.'})
        except Exception as e:
            print(f"서버에서 이미지 처리 중 오류 발생: {e}")
            return JsonResponse({'success': False, 'message': f"오류 발생: {str(e)}"})

    return render(request, 'faces/face_registration.html')
