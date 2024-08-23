from django.shortcuts import render
from django.http import JsonResponse  
from PIL import Image
import mediapipe as mp
from facenet_pytorch import InceptionResnetV1
import torch
from torchvision import transforms
import base64
import io
import numpy as np
from faces.models import Faces
import json

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
    try:
        # Base64 인코딩된 이미지 데이터에서 헤더 제거
        if ',' in image:
            header, image_data = image.split(',')
        else:
            image_data = image
        
        print(f"Base64 데이터 길이: {len(image_data)}")  # 데이터 길이 출력
        decoded_image_data = base64.b64decode(image_data)

        # PIL을 사용하여 디코딩된 이미지를 열기
        image_pil = Image.open(io.BytesIO(decoded_image_data))

        # 이미지 변환 및 임베딩 추출
        image_tensor = transform(image_pil).unsqueeze(0).to(device)
        
        with torch.no_grad():
            embedding = model(image_tensor)
        
        return embedding.cpu().numpy().flatten()

    except Exception as e:
        print(f"이미지 처리 중 오류 발생: {str(e)}")
        raise ValueError(f"이미지를 처리하는 중 오류 발생: {str(e)}")

def recognize_face(request):
    if request.method == 'POST':
        try:
            # 로그 출력 추가
            print("POST 요청이 수신되었습니다.")

            body_unicode = request.body.decode('utf-8')
            body_data = json.loads(body_unicode)
            image = body_data.get('image')

            print("이미지 데이터가 수신되었습니다.")

            test_embedding = get_embedding_from_image(image)

            # 모든 사용자의 얼굴 데이터를 가져오기
            face_instances = Faces.objects.all()

            if not face_instances.exists():
                print("등록된 얼굴 데이터가 없습니다.")
                return JsonResponse({'success': False, 'message': '등록된 얼굴 데이터가 없습니다.'})
            
            # 모든 얼굴 데이터와 비교하여 가장 유사한 것을 찾음
            min_dist = float('inf')
            best_accuracy = 0
            matched_user_id = None

            for face_instance in face_instances:
                # face_data를 numpy 배열로 변환
                face_data_array = np.frombuffer(face_instance.face_data, dtype=np.float32)
                
                # test_embedding과 face_data_array를 비교
                dist = np.linalg.norm(test_embedding - face_data_array)
                accuracy = 100 - dist  # 유사도를 기반으로 정확도 계산

                if dist < min_dist:
                    min_dist = dist
                    best_accuracy = accuracy
                    matched_user_id = face_instance.user_id

            print(f"최소 거리: {min_dist}, 최고 정확도: {best_accuracy}, 일치하는 사용자 ID: {matched_user_id}")

            if best_accuracy > 95:  # 임계값으로 정확도 판단
                user_name = "사용자"  # 기본 이름 설정
                if matched_user_id is not None:
                    matched_user = Faces.objects.get(user_id=matched_user_id)
                    user_name = matched_user.user.username
                return JsonResponse({'success': True, 'message': f'{user_name}님 인증되었습니다.', 'accuracy': f'{best_accuracy:.2f}%'})
            else:
                return JsonResponse({'success': False, 'message': '얼굴 인증 실패', 'accuracy': f'{best_accuracy:.2f}%'})

        except Exception as e:
            print(f"오류 발생: {str(e)}")
            return JsonResponse({'success': False, 'message': f"오류 발생: {str(e)}"})

    return render(request, 'field/face_recognize.html')
