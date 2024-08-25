from django.shortcuts import render, redirect
from .models import ReservationDelivery
from common.models import Reservations, Locations, Lockers
from django.utils.dateparse import parse_datetime
from django.urls import reverse
from django.contrib.auth.decorators import login_required

@login_required
def select_delivery_location(request):
    if request.method == 'POST':
        start_city = request.POST.get('start_city')
        start_district = request.POST.get('start_district')
        end_city = request.POST.get('end_city')
        end_district = request.POST.get('end_district')

        print("POST Data:", start_city, start_district, end_city, end_district)  # 디버깅: POST 데이터 확인

        if start_city and start_district and end_city and end_district:
            start_location = Locations.objects.filter(city=start_city, district=start_district).first()
            end_location = Locations.objects.filter(city=end_city, district=end_district).first()

            if start_location and end_location:
                # 디버깅: 세션에 저장된 location_id 확인
                print("Start Location ID:", start_location.location_id)
                print("End Location ID:", end_location.location_id)

                request.session['start_location_id'] = start_location.location_id
                request.session['end_location_id'] = end_location.location_id

                return redirect('reservation_delivery:select_date_time')
            else:
                print("Start or End Location Not Found")  # 디버깅: 위치를 찾지 못한 경우
        else:
            print("Missing POST Data")  # 디버깅: POST 데이터 누락

    locations = {
        '서울': ['강남구', '강동구', '구로구', '종로구', '동대문구', '중구'],
        '경기': ['수원시', '성남시', '고양시', '용인시', '부천시', '안산시'],
        '인천': ['계양구', '남동구', '동구', '미추홀구', '부평구', '서구'],
        '강원': ['춘천시', '원주시', '강릉시', '동해시', '삼척시', '태백시'],
        '부산/울산': ['해운대구', '남구', '동구', '북구', '부산진구', '기장군'],
    }

    return render(request, 'reservation_delivery/select_delivery_location.html', {'locations': locations})


@login_required
def select_date_time(request):
    if request.method == 'POST':
        start_datetime = request.POST.get('start_datetime')
        end_datetime = request.POST.get('end_datetime')
        request.session['start_datetime'] = start_datetime
        request.session['end_datetime'] = end_datetime
        return redirect('reservation_delivery:select_delivery_locker')
    return render(request, 'reservation_delivery/select_date_time.html')

@login_required
def select_delivery_locker(request):
    if request.method == 'POST':
        start_location_id = request.POST.get('start_location_id')
        start_locker_id = request.POST.get('start_locker_id')
        end_location_id = request.POST.get('end_location_id')
        end_locker_id = request.POST.get('end_locker_id')

        # 폼 데이터가 제대로 전달되었는지 확인
        print("Start Location ID:", start_location_id)
        print("End Location ID:", end_location_id)
        print("Start Locker ID:", start_locker_id)
        print("End Locker ID:", end_locker_id)

        if not (start_location_id and start_locker_id and end_location_id and end_locker_id):
            return render(request, 'reservation_delivery/select_lockers.html', {
                'error': '모든 보관함과 위치를 선택해야 합니다.'
            })

        try:
            start_location = Locations.objects.get(pk=start_location_id)
            end_location = Locations.objects.get(pk=end_location_id)
            start_locker = Lockers.objects.get(pk=start_locker_id)
            end_locker = Lockers.objects.get(pk=end_locker_id)
        except Locations.DoesNotExist:
            return render(request, 'reservation_delivery/select_lockers.html', {
                'error': '지정된 위치를 찾을 수 없습니다.',
            })
        except Lockers.DoesNotExist:
            return render(request, 'reservation_delivery/select_lockers.html', {
                'error': '지정된 보관함을 찾을 수 없습니다.',
            })

        if request.method == 'POST':
        # 새로운 예약 생성
            reservation = Reservations.objects.create(
                user=request.user,
                start_location=start_location,
                end_location=end_location,
                start_locker=start_locker,
                end_locker=end_locker,
                start_datetime=parse_datetime(request.session['start_datetime']),
                end_datetime=parse_datetime(request.session['end_datetime']),
                status='reserved',
                reservation_type='delivery'
            )
            reservation.save()

            # ReservationDelivery 생성
            ReservationDelivery.objects.create(
                reservation=reservation,
                start_location=start_location,
                end_location=end_location,
                start_locker=start_locker,
                end_locker=end_locker,
                delivery_fee=3000.00,  # 예시로 배송비 설정
                user=request.user
            )

            return redirect('reservation_delivery:delivery_reservation_complete')

    else:
        start_location_id = request.session.get('start_location_id')
        end_location_id = request.session.get('end_location_id')
        start_datetime_str = request.session.get('start_datetime')
        end_datetime_str = request.session.get('end_datetime')

        start_datetime = parse_datetime(start_datetime_str)
        end_datetime = parse_datetime(end_datetime_str)

        start_lockers = Lockers.objects.filter(location_id=start_location_id)
        reserved_start_lockers = Reservations.objects.filter(
            start_datetime__lt=end_datetime,
            end_datetime__gt=start_datetime,
            start_location_id=start_location_id
        ).values_list('start_locker_id', flat=True)

        start_locker_statuses = [
            (locker, 'occupied' if locker.locker_id in reserved_start_lockers else 'available')
            for locker in start_lockers
        ]

        end_lockers = Lockers.objects.filter(location_id=end_location_id)
        reserved_end_lockers = Reservations.objects.filter(
            start_datetime__lt=end_datetime,
            end_datetime__gt=start_datetime,
            end_location_id=end_location_id
        ).values_list('end_locker_id', flat=True)

        end_locker_statuses = [
            (locker, 'occupied' if locker.locker_id in reserved_end_lockers else 'available')
            for locker in end_lockers
        ]

        context = {
            'start_datetime': start_datetime,
            'end_datetime': end_datetime,
            'start_locker_statuses': start_locker_statuses,
            'end_locker_statuses': end_locker_statuses,
            'start_location_id': start_location_id,
            'end_location_id': end_location_id,
        }

        return render(request, 'reservation_delivery/select_lockers.html', context)


@login_required
def delivery_reservation_complete(request):
    reservation = Reservations.objects.filter(user=request.user).last()

    if reservation is None:
        return render(request, 'reservation_delivery/delivery_reservation_complete.html', {
            'error': '예약된 정보가 없습니다.'
        })

    return render(request, 'reservation_delivery/delivery_reservation_complete.html', {
        'reservation': reservation,
    })

def view_delivery_reservations(request):
    reservations = Reservations.objects.filter(user=request.user).last()  # 가장 최근 예약 가져오기
    return render(request, 'reservation_delivery/delivery_list.html', {'reservations': reservations})