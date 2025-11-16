import unittest
from unittest.mock import patch, Mock
import requests
from FineDustInfo import get_grade, get_air_quality, display_air_quality

# ----------------------------------------------------------------------------

# get_grade() 테스트
class TestGetGrade(unittest.TestCase):

    def test_pm10_grades(self):
        """PM10 (미세먼지) 등급 테스트"""
        print("테스트: PM10 등급")
        # self.assertEqual(기대값, 실제값) [cite: 301]
        self.assertEqual(get_grade('25', 'pm10'), "① 좋음 😃")
        self.assertEqual(get_grade('50', 'pm10'), "② 보통 🙂")
        self.assertEqual(get_grade('100', 'pm10'), "③ 나쁨 😷")
        self.assertEqual(get_grade('200', 'pm10'), "④ 매우 나쁨 👿")

    def test_pm25_grades(self):
        """PM2.5 (초미세먼지) 등급 테스트"""
        print("테스트: PM2.5 등급")
        self.assertEqual(get_grade('10', 'pm25'), "① 좋음 😃")
        self.assertEqual(get_grade('20', 'pm25'), "② 보통 🙂")
        self.assertEqual(get_grade('50', 'pm25'), "③ 나쁨 😷")
        self.assertEqual(get_grade('100', 'pm25'), "④ 매우 나쁨 👿")

    def test_missing_value(self):
        """'-' 또는 None 값 처리 테스트"""
        print("테스트: 결측치")
        self.assertEqual(get_grade('-', 'pm10'), "정보 없음")
        self.assertEqual(get_grade(None, 'pm25'), "정보 없음")

# get_air_quality() 테스트
class TestGetAirQuality(unittest.TestCase):

    # 가짜 API 응답 데이터
    def setUp(self):
        self.fake_success_data = {
            'response': {
                'header': {'resultCode': '00', 'resultMsg': 'NORMAL_SERVICE'},
                'body': {
                    'items': [
                        {
                            'stationName': '가짜측정소',
                            'dataTime': '2025-11-16 19:00',
                            'pm10Value': '50', # '보통'
                            'pm25Value': '20'  # '보통'
                        }
                    ]
                }
            }
        }
    
    @patch('FineDustInfo.requests.get')
    def test_get_air_quality_success(self, mock_requests_get):
        """API 호출 성공 케이스 테스트"""
        print("테스트: API 호출 성공")
        
        # Mock 설정
        mock_response = Mock()
        mock_response.status_code = 200
        # .json()가 self.fake_success_data를 반환하도록 설정
        mock_response.json.return_value = self.fake_success_data
        
        # 'requests.get'이 호출되면 미리 만든 'mock_response'를 반환
        mock_requests_get.return_value = mock_response

        # 실제 함수 호출
        result_data = get_air_quality('서울')

        # 검증
        # requests.get이 올바른 인자로 호출되었는지 확인
        mock_requests_get.assert_called_once() # 1번 호출되었는지
        call_args = mock_requests_get.call_args
        self.assertIn('sidoName', call_args.kwargs['params'])
        self.assertEqual(call_args.kwargs['params']['sidoName'], '서울')
        
        # 함수가 의도한 가짜 데이터를 반환했는지 확인
        self.assertEqual(result_data, self.fake_success_data)

    @patch('FineDustInfo.requests.get')
    def test_get_air_quality_api_error(self, mock_requests_get):
        """API 자체가 404 등 오류를 반환하는 케이스 테스트"""
        print("테스트: API 404 오류")
        
        # Mock 설정
        mock_response = Mock()
        mock_response.status_code = 404
        # 404 오류 시 .raise_for_status()가 HTTPError를 발생시키도록 설정
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        
        mock_requests_get.return_value = mock_response

        # 실제 함수 호출
        result_data = get_air_quality('없는도시')

        # 검증
        # 함수가 오류를 인지하고 None을 반환했는지 확인
        self.assertIsNone(result_data)

# display_air_quality() 테스트
class TestDisplayAirQuality(unittest.TestCase):

    def setUp(self):

        # 가짜 API 응답 데이터
        self.test_data = {
            'response': {
                'body': {
                    'items': [
                        {
                            'stationName': '가짜측정소',
                            'dataTime': '2025-11-16 19:00',
                            'pm10Value': '50',
                            'pm25Value': '20'
                        }
                    ]
                }
            }
        }

    @patch('builtins.print')
    def test_display_output(self, mock_print):
        """출력 함수가 올바른 내용을 print하는지 테스트"""
        print("테스트: print() 출력 내용")
        
        # 실제 함수 호출
        display_air_quality(self.test_data)

        # 검증
        # mock_print.call_args_list에 print가 호출된 모든 기록이 리스트로 남음
        
        # call_args_list의 첫 번째 호출(call[0])의 첫 번째 인자(call[0][0])를 문자열로 만들기
        all_calls = [str(call[0][0]) for call in mock_print.call_args_list]
        
        # print된 내용 중에 '가짜측정소'라는 문자열이 포함되어 있는지 확인
        self.assertTrue(any("가짜측정소" in call for call in all_calls))
        # print된 내용 중에 'PM10' 등급인 '② 보통'이 포함되어 있는지 확인
        self.assertTrue(any("② 보통" in call for call in all_calls))

# ------------------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main()