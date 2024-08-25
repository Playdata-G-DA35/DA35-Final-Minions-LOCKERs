from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from facenet_pytorch import MTCNN, InceptionResnetV1
import torch
import base64
import io
import numpy as np
from PIL import Image
from .models import Faces
from scipy.spatial.distance import cosine
import json

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

mtcnn = MTCNN(
    image_size=160,  # 얼굴 크기 조정
    margin=0,        # 얼굴 주변 마진
    min_face_size=20,  # 감지할 최소 얼굴 크기
    thresholds=[0.6, 0.7, 0.7],  # 단계별 감지 임계값 (세 개의 네트워크에 대한 값)
    factor=0.709,    # 이미지 피라미드 크기 조정 계수
    device=device
)
model = InceptionResnetV1(pretrained='vggface2', classify=False).eval().to(device)

def get_embedding_from_image(image, index=None):
    try:
        image_pil = Image.open(io.BytesIO(base64.b64decode(image.split(',')[1])))
        
        # 이미지 해상도 줄이기
        image_pil = image_pil.resize((image_pil.width // 2, image_pil.height // 2))

        if index is not None:
            image_pil.save(f'debug_image_{index}.jpg')

        img_cropped = mtcnn(image_pil)
        if img_cropped is None:
            raise ValueError("얼굴을 감지할 수 없습니다.")

        img_cropped = img_cropped.unsqueeze(0).to(device)
        with torch.no_grad():
            embedding = model(img_cropped)
        
        return embedding.cpu().numpy().flatten()

    except Exception as e:
        print(f"이미지 처리 중 오류 발생 (이미지 {index}): {str(e)}")
        return None



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
                embedding = get_embedding_from_image(image, index=i+1)
                if embedding is not None:
                    embeddings.append(embedding)
                    print(f"{i+1}/17 각도 이미지 임베딩 추출 완료")
                else:
                    print(f"{i+1}/17 이미지에서 얼굴을 감지하지 못했습니다.")

            if len(embeddings) != 17:
                return JsonResponse({'success': False, 'message': '일부 이미지에서 얼굴 감지 실패, 다시 시도해주세요.'})

            face_instance = Faces(
                user=request.user,
                face_data_1=embeddings[0],
                face_data_2=embeddings[1],
                face_data_3=embeddings[2],
                face_data_4=embeddings[3],
                face_data_5=embeddings[4],
                face_data_6=embeddings[5],
                face_data_7=embeddings[6],
                face_data_8=embeddings[7],
                face_data_9=embeddings[8],
                face_data_10=embeddings[9],
                face_data_11=embeddings[10],
                face_data_12=embeddings[11],
                face_data_13=embeddings[12],
                face_data_14=embeddings[13],
                face_data_15=embeddings[14],
                face_data_16=embeddings[15],
                face_data_17=embeddings[16],
            )
            face_instance.save()
            print("모든 각도의 임베딩 값이 성공적으로 DB에 저장되었습니다.")

            return JsonResponse({'success': True, 'message': '임베딩이 성공적으로 저장되었습니다.'})
        except Exception as e:
            print(f"서버에서 이미지 처리 중 오류 발생: {e}")
            return JsonResponse({'success': False, 'message': f"오류 발생: {str(e)}"})

    return render(request, 'faces/face_registration.html')
