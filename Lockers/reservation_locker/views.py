from django.shortcuts import render, redirect
from .models import ReservationLocker
from common.models import Reservations, Locations, Lockers
from django.utils.dateparse import parse_datetime
from django.urls import reverse
from django.contrib.auth.decorators import login_required

@login_required
def select_location(request):
    if request.method == 'POST':
        selected_city = request.POST.get('selected_city')
        selected_district = request.POST.get('selected_district')

        if selected_city and selected_district:
            location = Locations.objects.filter(city=selected_city, district=selected_district).first()
            if location:
                request.session['selected_location_id'] = location.location_id
                print(f"Location ID stored in session: {location.location_id}")
                return redirect('reservation_locker:select_date_time')

    locations = {
        '서울': ['강남구', '강동구', '구로구', '종로구', '동대문구', '중구'],
        '경기': ['수원시', '성남시', '고양시', '용인시', '부천시', '안산시'],
        '인천': ['계양구', '남동구', '동구', '미추홀구', '부평구', '서구'],
        '강원': ['춘천시', '원주시', '강릉시', '동해시', '삼척시', '태백시'],
        '부산/울산': ['해운대구', '남구', '동구', '북구', '부산진구', '기장군'],
    }
    
    return render(request, 'reservation_locker/select_location.html', {'locations': locations})

@login_required
def select_date_time(request):
    if request.method == 'POST':
        start_datetime = request.POST.get('start_datetime')
        end_datetime = request.POST.get('end_datetime')
         # 로그 출력으로 값 확인
        print("Start datetime received:", start_datetime)
        print("End datetime received:", end_datetime)
        request.session['start_datetime'] = start_datetime
        request.session['end_datetime'] = end_datetime
        print(f"Start datetime stored in session: {start_datetime}")  # 로그 추가
        print(f"End datetime stored in session: {end_datetime}")  # 로그 추가
        return redirect('reservation_locker:select_locker')
    return render(request, 'reservation_locker/select_date_time.html')

@login_required
def select_locker(request):
    location_id = request.session.get('selected_location_id')
    start_datetime_str = request.session.get('start_datetime')
    end_datetime_str = request.session.get('end_datetime')
    
    # 로그 추가
    print(f"Location ID: {location_id}")
    print(f"Start Datetime: {start_datetime_str}")
    print(f"End Datetime: {end_datetime_str}")

      # None 값 확인 후 처리
    if not location_id or not start_datetime_str or not end_datetime_str:
        return redirect('reservation_locker:select_date_time')

    start_datetime = parse_datetime(start_datetime_str)
    end_datetime = parse_datetime(end_datetime_str)

    lockers = Lockers.objects.filter(location_id=location_id)
    reserved_lockers = Reservations.objects.filter(
        start_datetime__lt=end_datetime,
        end_datetime__gt=start_datetime,
        start_location_id=location_id,
        end_location_id=location_id
    ).values_list('start_locker_id', flat=True)

    available_lockers = lockers.exclude(locker_id__in=reserved_lockers)

    locker_statuses = [
        (locker, 'occupied' if locker.locker_id in reserved_lockers else 'available')
        for locker in lockers
    ]

    if request.method == 'POST':
        selected_locker = request.POST.get('selected_locker')
        reservation = Reservations.objects.create(
            user=request.user,
            start_locker_id=selected_locker,
            end_locker_id=selected_locker,
            start_location_id=location_id,
            end_location_id=location_id,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            status='reserved',
            reservation_type='locker'
        )
        reservation.save()  # 명시적으로 예약 정보 저장

        ReservationLocker.objects.create(
            reservation=reservation,
            locker_id=selected_locker,
            location_id=location_id,
            user=request.user
        )
        return redirect('reservation_locker:locker_reservation_complete')

    context = {
        'start_datetime': start_datetime,
        'end_datetime': end_datetime,
        'locker_statuses': locker_statuses,
    }
    return render(request, 'reservation_locker/select_locker.html', context)

@login_required
def locker_reservation_complete(request):
    # 예약 완료 후, 얼굴 등록 버튼 추가
    reservation = Reservations.objects.filter(user=request.user).last()
    
    if reservation is None:
        return render(request, 'reservation_locker/locker_reservation_complete.html', {
            'error': '예약된 정보가 없습니다.'
        })
    
    return render(request, 'reservation_locker/locker_reservation_complete.html', {
        'reservation': reservation,
    })

def view_locker_reservations(request):
    reservations = Reservations.objects.filter(user=request.user).last()  # 가장 최근 예약 가져오기
    return render(request, 'reservation_locker/locker_list.html', {'reservations': reservations})
