import requests
import json
import sys

# -------------------------------------------------------------------------------------------
SERVICE_KEY = "909abcfd34beb0554ea3d97a7d343f7f495be3243f0d0b85c61908ffe3cf9e88" 
# -------------------------------------------------------------------------------------------
BASE_URL = "https://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getCtprvnRltmMesureDnsty"
# -------------------------------------------------------------------------------------------

def get_air_quality(sido_name):
    """
    주어진 시/도 이름으로 에어코리아 API에 대기오염 정보를 요청
    
    Args:
        sido_name (str): 시/도 이름 (예: "서울", "경기", "광주")

    Returns:
        dict: API로부터 받은 대기오염 데이터 (JSON)
        None: API 요청 실패 시
    """
    
    params = {
        'serviceKey': SERVICE_KEY,
        'returnType': 'json',
        'sidoName': sido_name,
        'ver': '1.0',         # 데이터 버전 (문서에 명시된 대로)
        'numOfRows': 100,     # 한 페이지에 많은 결과(측정소)를 받기 위해
        'pageNo': 1
    }

    try:
        # requests.get을 사용하여 API에 GET 요청 전송
        response = requests.get(BASE_URL, params=params)
        
        # HTTP 상태 코드 확인
        if response.status_code != 200:
            print(f"❌ 오류: API 요청 실패 (상태 코드: {response.status_code})")
            print(response.text) # 오류 메시지
            return None
        
        # JSON 응답을 파이썬 딕셔너리로 변환
        data = response.json()
        
        # API 자체의 응답 상태 확인
        if data['response']['header']['resultCode'] != '00':
            error_msg = data['response']['header']['resultMsg']
            print(f"❌ API 오류: {error_msg}")
            
            # 서비스 키 오류 처리
            if "SERVICE_KEY_IS_NOT_REGISTERED_ERROR" in error_msg:
                print("🚨 (확인) 서비스 키가 잘못되었습니다. 1단계에서 '디코딩'된 키를 복사했는지 확인하세요.")
            return None

        return data

    except requests.exceptions.RequestException as err:
        print(f"❌ 오류: 네트워크 연결에 실패했습니다. {err}")
        return None
    except json.JSONDecodeError:
        print("❌ 오류: API 응답을 JSON으로 파싱할 수 없습니다.")
        print(f"받은 응답 내용: {response.text[:200]}...") # 받은 내용 일부 출력
        return None

def get_grade(value, type):
    """
    수치(str)를 받아 '좋음', '보통' 등의 등급(str)으로 변환
    (수치가 '-'이거나 None일 수 있음)
    
    Args:
        value (str): 미세먼지 또는 초미세먼지 수치 문자열
        type (str): 'pm10' (미세) 또는 'pm25' (초미세)
    """
    if value is None or value == '-':
        return "정보 없음"

    try:
        v = int(value)
    except ValueError:
        return f"({value}) 값 오류"

    # 기준에 따라 등급 반환 (환경부 기준)
    if type == 'pm10': # 미세먼지
        if 0 <= v <= 30: return "① 좋음 😃"
        if 31 <= v <= 80: return "② 보통 🙂"
        if 81 <= v <= 150: return "③ 나쁨 😷"
        if v >= 151: return "④ 매우 나쁨 👿"
    elif type == 'pm25': # 초미세먼지
        if 0 <= v <= 15: return "① 좋음 😃"
        if 16 <= v <= 35: return "② 보통 🙂"
        if 36 <= v <= 75: return "③ 나쁨 😷"
        if v >= 76: return "④ 매우 나쁨 👿"
        
    return "기준 없음"


def display_air_quality(air_data):
    """
    파싱된 대기오염 데이터를 사용자 친화적인 형태로 터미널에 출력
    """
    if air_data is None:
        return

    try:
        # JSON 데이터에서 실제 측정소 'items' 리스트 추출
        items = air_data['response']['body']['items']
        
        if not items:
            print("데이터가 없습니다. (해당 시/도에 측정소가 없거나 API 문제)")
            return
            
        # '시도별' API는 해당 시/도의 *모든* 측정소 정보를 리스트로 반환
        # 여기서는 편의상 첫 번째 측정소의 데이터만 보여줌
        
        # (심화 학습: 사용자가 '구' 이름을 입력하면 items를 순회하며 해당 구의 측정소를 찾을 수 있음)
        
        item = items[0] # 첫 번째 측정소 데이터
        
        station = item.get('stationName', '알 수 없음')
        data_time = item.get('dataTime', '알 수 없음')
        pm10_value = item.get('pm10Value', '-') # 미세먼지 (PM10)
        pm25_value = item.get('pm25Value', '-') # 초미세먼지 (PM2.5)

        # 등급 계산
        pm10_grade = get_grade(pm10_value, 'pm10')
        pm25_grade = get_grade(pm25_value, 'pm25')
        
        # 터미널에 출력
        print("\n" + "="*35)
        print(f" 📍  측정소: {station} (측정 시각: {data_time})")
        print("="*35)
        print(f" 💨  미세먼지 (PM10):   {pm10_value} ㎍/m³  ({pm10_grade})")
        print(f" 🌪️  초미세먼지 (PM2.5): {pm25_value} ㎍/m³  ({pm25_grade})")
        print("\n" + "-"*35)
        print(f"* {len(items)}개 측정소 중 첫 번째 정보를 표시합니다.")
        print("="*35 + "\n")

    except KeyError as e:
        print(f"❌ 오류: 응답 데이터 파싱에 실패했습니다. (키: {e})")
        print("API 응답 형식이 변경되었을 수 있습니다.")
    except IndexError as e:
        print(f"❌ 오류: 측정소 'items' 데이터를 찾지 못했습니다.")


def main():
    
    if SERVICE_KEY == "YOUR_SERVICE_KEY_HERE":
        print("🛑 경고: 코드 상단의 'SERVICE_KEY' 변수에 본인의 공공데이터포털 API 키를 입력하세요.")
        print("1. https://www.data.go.kr/ 접속")
        print("2. '대기오염정보' 검색 후 '한국환경공단' API 활용신청")
        print("3. [마이페이지] > [일반 인증키 (Decoded)] 키 복사 후 붙여넣기")
        sys.exit(1) # 프로그램 종료

    print("--- 🌫️  실시간 미세먼지 알리미 (에어코리아) ---")
    
    # 공공데이터 API가 지원하는 시/도 이름 목록
    valid_sido = ["서울", "부산", "대구", "인천", "광주", "대전", "울산", 
                  "경기", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주", "세종"]
    
    while True:
        print("\n조회 가능한 시/도: ")
        print(", ".join(valid_sido))
        sido_name = input("조회할 시/도 이름을 입력하세요 (종료: 'exit' 또는 'q'): ")
        
        if sido_name.lower() in ('exit', 'q'):
            print("👋 프로그램을 종료합니다.")
            break
            
        if not sido_name:
            print("시/도 이름을 입력해주세요.")
            continue
            
        if sido_name not in valid_sido:
            print(f"❌ 잘못된 시/도 이름입니다. 목록에 있는 이름 중 하나를 정확히 입력하세요.")
            continue
            
        print(f"\n'{sido_name}' 지역의 대기오염 정보를 조회합니다...")
        data = get_air_quality(sido_name)
        display_air_quality(data)

if __name__ == "__main__":
    main()