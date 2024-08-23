# common/management/commands/add_locations_and_lockers.py
from django.core.management.base import BaseCommand
from common.models import Locations, Lockers

class Command(BaseCommand):
    help = 'Add predefined locations and lockers'

    def handle(self, *args, **kwargs):
        location_data = {
            '서울': ['강남구', '강동구', '구로구', '종로구', '동대문구', '중구'],
            '경기': ['수원시', '성남시', '고양시', '용인시', '부천시', '안산시'],
            '인천': ['계양구', '남동구', '동구', '미추홀구', '부평구', '서구'],
            '강원': ['춘천시', '원주시', '강릉시', '동해시', '삼척시', '태백시'],
            '부산/울산': ['해운대구', '남구', '동구', '북구', '부산진구', '기장군'],
        }

        for city, districts in location_data.items():
            for district in districts:
                location, created = Locations.objects.get_or_create(city=city, district=district, defaults={
                    'address': f"{city} {district} 주소"
                })
                if created:
                    self.stdout.write(self.style.SUCCESS(f"Location created: {location}"))
                else:
                    self.stdout.write(self.style.WARNING(f"Location already exists: {location}"))

                # 각 위치에 64개의 보관함 생성
                for locker_number in range(1, 65):
                    locker, created = Lockers.objects.get_or_create(locker_number=locker_number, location=location, defaults={
                        'status': 'available'
                    })
                    if created:
                        self.stdout.write(self.style.SUCCESS(f"Locker {locker_number} created at {location}"))
                    else:
                        self.stdout.write(self.style.WARNING(f"Locker {locker_number} already exists at {location}"))

        self.stdout.write(self.style.SUCCESS('Locations and lockers added successfully.'))
