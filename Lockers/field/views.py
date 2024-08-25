from django.shortcuts import render, redirect
from django.http import JsonResponse
from PIL import Image
from facenet_pytorch import MTCNN, InceptionResnetV1
import torch
import base64
import io
import numpy as np
from faces.models import Faces
from scipy.spatial.distance import cosine
import json
import cv2
import dlib
from torchvision.models import resnet34, ResNet34_Weights
import torch.nn as nn
import torchvision.transforms as transforms

# 디바이스 설정 (GPU가 있으면 사용, 없으면 CPU)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 얼굴 인식 모델 설정
mtcnn = MTCNN(
    image_size=160,
    margin=0,
    min_face_size=20,
    thresholds=[0.6, 0.7, 0.7],
    factor=0.709,
    device=device
)
model = InceptionResnetV1(pretrained='vggface2', classify=False).eval().to(device)

# Face classification 모델 설정
weights = ResNet34_Weights.DEFAULT
class_model = resnet34(weights=weights)
class_model.fc = nn.Linear(class_model.fc.in_features, 18)  # 18개의 출력 노드로 설정
class_model.load_state_dict(torch.load(r'C:\Users\USER\OneDrive\classes\LOCKERs\FairFace\res34_fair_align_multi_7_20190809.pt', map_location=device, weights_only=True))
class_model = class_model.to(device)
class_model.eval()

# 얼굴 탐지기를 위한 dlib 설정
detector = dlib.get_frontal_face_detector()

# 이미지 전처리 설정
transform = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

def get_embedding_from_image(image):
    try:
        image_pil = Image.open(io.BytesIO(base64.b64decode(image.split(',')[1])))

        img_cropped = mtcnn(image_pil)
        if img_cropped is None:
            raise ValueError("얼굴을 감지할 수 없습니다.")

        img_cropped = img_cropped.unsqueeze(0).to(device)
        with torch.no_grad():
            embedding = model(img_cropped)

        return embedding.cpu().numpy().flatten()

    except Exception as e:
        print(f"이미지 처리 중 오류 발생: {str(e)}")
        raise ValueError(f"이미지를 처리하는 중 오류 발생: {str(e)}")

def classify_face(image):
    with torch.no_grad():
        input_tensor = transform(image).unsqueeze(0).to(device)
        outputs = class_model(input_tensor)

        race_scores = torch.softmax(outputs[0][:7], dim=0)
        gender_scores = torch.softmax(outputs[0][7:9], dim=0)
        age_scores = torch.softmax(outputs[0][9:18], dim=0)

        race_pred = torch.argmax(race_scores).item()
        gender_pred = torch.argmax(gender_scores).item()
        age_pred = torch.argmax(age_scores).item()

        race = ['White', 'Black', 'Latino_Hispanic', 'East Asian', 'Southeast Asian', 'Indian', 'Middle Eastern'][race_pred]
        gender = 'Male' if gender_pred == 0 else 'Female'
        age = ["0-2", "3-9", "10-19", "20-29", "30-39", "40-49", "50-59", "60-69", "70+"][age_pred]

        return race, gender, age

def determine_keyword(gender, age):
    # 10~49 세를 "10-49"로 묶고, 50세 이상을 "50+"로 묉습니다.
    age_group = "10-49" if age in ["10-19", "20-29", "30-39", "40-49"] else "50+"

    # 성별과 나이대에 따라 키워드를 결정합니다.
    if gender == "Male" and age_group == "10-49":
        return "편의점"
    elif gender == "Male" and age_group == "50+":
        return "술집"
    elif gender == "Female" and age_group == "10-49":
        return "맛집"
    elif gender == "Female" and age_group == "50+":
        return "찜질방"
    else:
        return "용산 맛집"  # 기본 키워드

def recognize_face(request):
    if request.method == 'POST':
        try:
            print("POST 요청이 수신되었습니다.")

            body_unicode = request.body.decode('utf-8')
            body_data = json.loads(body_unicode)
            image = body_data.get('image')

            print("이미지 데이터가 수신되었습니다.")

            # 임베딩 추출
            test_embedding = get_embedding_from_image(image)

            # 기존의 얼굴 데이터와 비교
            face_instances = Faces.objects.all()
            if not face_instances.exists():
                print("등록된 얼굴 데이터가 없습니다.")
                return JsonResponse({'success': False, 'message': '등록된 얼굴 데이터가 없습니다.'})

            best_similarity = -1
            matched_user_id = None

            for face_instance in face_instances:
                for i in range(1, 18):
                    face_data_array = np.frombuffer(getattr(face_instance, f'face_data_{i}'), dtype=np.float32)
                    similarity = 1 - cosine(test_embedding, face_data_array)
                    if similarity > best_similarity:
                        best_similarity = similarity
                        matched_user_id = face_instance.user_id

            threshold = 0.5
            if best_similarity > threshold:
                user_name = "사용자"
                if matched_user_id is not None:
                    matched_user = Faces.objects.get(user_id=matched_user_id)
                    user_name = matched_user.user.username

                # 인증 성공 시 사용자 정보를 포함하여 JSON 응답 반환
                return JsonResponse({'success': True, 'message': f'{user_name}님 인증되었습니다.'})
            else:
                return JsonResponse({'success': False, 'message': '얼굴 인증 실패', 'similarity': f'{best_similarity:.2f}'})

        except Exception as e:
            print(f"오류 발생: {str(e)}")
            return JsonResponse({'success': False, 'message': f"오류 발생: {str(e)}"})

    return render(request, 'field/face_recognize.html')

def classify_face_view(request):
    if request.method == 'POST':
        try:
            body_unicode = request.body.decode('utf-8')
            body_data = json.loads(body_unicode)
            image = body_data.get('image')

            image_pil = Image.open(io.BytesIO(base64.b64decode(image.split(',')[1])))
            race, gender, age = classify_face(np.array(image_pil))

            print(f"성별: {gender}, 나이대: {age}")

            keyword = determine_keyword(gender, age)

            return JsonResponse({'keyword': keyword})
        except Exception as e:
            print(f"오류 발생: {str(e)}")
            return JsonResponse({'error': str(e)})

    return JsonResponse({'error': 'Invalid request method.'})

def map_view(request):
    keyword = request.GET.get('keyword', '용산 맛집')
    return render(request, 'field/map.html', {'keyword': keyword})
