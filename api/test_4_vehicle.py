from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
# モデルとシリアライザー
from .models import Vehicle, Brand, Segment
from .serializers import VehicleSerializer
from decimal import Decimal

SEGMENTS_URL = '/api/segments/'
BRANDS_URL = '/api/brands/'
VEHICLES_URL = '/api/vehicles/'

# セグメントを作成するための関数
def create_segment(segment_name):
    return Segment.objects.create(segment_name=segment_name)

# ブランドを作成するための関数
def create_brand(brand_name):
    return Brand.objects.create(brand_name=brand_name)

# 車種を作成するための関数
# paramsにはuser以外の属性を持っている
def create_vehicle(user, **params):
    # 登録するデータのうち、固定値
    defaults = {
        'vehicle_name': 'MODEL S',
        'release_year': 2019,
        'price': 500.12,
    }
    # パラメータを登録するデータに追加する
    defaults.update(params)

    return Vehicle.objects.create(user=user, **defaults)

# キーを含むURLを作成する　（reverseはURLのパスを生成する）
def detail_seg_url(segment_id):
    return reverse('api:segment-detail', args=[segment_id])

# キーを含むURLを作成する　（reverseはURLのパスを生成する）
def detail_brand_url(brand_id):
    return reverse('api:brand-detail', args=[brand_id])

# キーを含むURLを作成する　（reverseはURLのパスを生成する）
def detail_vehicle_url(vehicle_id):
    return reverse('api:vehicle-detail', args=[vehicle_id])

## ==================================================================
## トークンの認証を通ったユーザでテストする
## ==================================================================
class AuthorizedVehicleApiTests(TestCase):
    # 各テストの最初に処理されるため、必要
    # 認証用のユーザ作成
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='dummy', password='dummy_pw')
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    # **************************************************************
    # GETメソッドで複数データが取得できる事を確認する。
    def test_4_1_should_get_vehicles(self):
        # segmentとbrandにテスト用のデータを登録しておく
        segment = create_segment(segment_name='Sedan')
        brand = create_brand(brand_name='Tesla')
        # vehicleに２レコード追加
        create_vehicle(user=self.user, segment=segment, brand=brand)
        create_vehicle(user=self.user, segment=segment, brand=brand)
        # GETメソッド実行
        res = self.client.get(VEHICLES_URL)
        # Vehicleの全データを取得する
        vehicles = Vehicle.objects.all().order_by('id')
        # Vehicleをシリアライザーを通した後のデータにする。（many=Trueは複数レコードの場合に指定する）
        serializer = VehicleSerializer(vehicles, many=True)
        # GETメソッドの結果が成功した事を確認する（HTTPステータスが200が返ってくる事を確認する）
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # 取得結果とセグメントのデータが一致するか確認する
        self.assertEqual(res.data, serializer.data)

    # **************************************************************
    # キーを指定したGETメソッドで１件のデータが取得できる事を確認する。
    def test_4_2_should_get_single_vehicle(self):
        # segmentとbrandにテスト用のデータを登録しておく
        segment = create_segment(segment_name='Sedan')
        brand = create_brand(brand_name='Tesla')
        # vehicleに１レコード追加
        vehicle = create_vehicle(user=self.user, segment=segment, brand=brand)
        # データ取得用のURLを設定する
        url = detail_vehicle_url(vehicle.id)
        # GETメソッド実行
        res = self.client.get(url)
        # vehicleをシリアライザーを通した後のデータにする。
        serializer = VehicleSerializer(vehicle)
        # GETメソッドの結果が成功した事を確認する（HTTPステータスが200が返ってくる事を確認する）
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # GETメソッドの取得結果と登録したデータが一致するか確認する
        self.assertEqual(res.data, serializer.data)

    # **************************************************************
    # 新規登録できる事を確認する
    def test_4_3_should_create_new_vehicle_successfully(self):
        # segmentとbrandにテスト用のデータを登録しておく
        segment = create_segment(segment_name='Sedan')
        brand = create_brand(brand_name='Tesla')
        # 新規登録するデータ
        payload = {
            'vehicle_name': 'MODEL S',
            'release_year': 2019,
            'price': 500.12,
            'segment': segment.id,
            'brand': brand.id,
        }
        # POSTメソッド実行
        res = self.client.post(VEHICLES_URL, payload)
        # データベースからPOSTメソッドの結果を検索する
        vehicle = Vehicle.objects.get(id=res.data['id'])
        # POSTメソッドの結果が成功した事を確認する（HTTPステータスが201が返ってくる事を確認する）
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        # 登録用に用意したデータと、POSTメソッドの結果を項目毎に比較して、一致する事を確認する。
        self.assertEqual(payload['vehicle_name'], vehicle.vehicle_name)
        self.assertEqual(payload['release_year'], vehicle.release_year)
        self.assertAlmostEqual(Decimal(payload['price']), vehicle.price, 2)
        self.assertEqual(payload['segment'], vehicle.segment.id)
        self.assertEqual(payload['brand'], vehicle.brand.id)

    # **************************************************************
    # brandが空白の場合はエラーになる事を確認する
    def test_4_4_should_not_create_vehicle_with_invalid(self):
        # segmentにテスト用のデータを登録しておく
        segment = create_segment(segment_name='Sedan')
        # 新規登録するデータ
        payload = {
            'vehicle_name': 'MODEL S',
            'release_year': 2019,
            'price': 500.00,
            'segment': segment.id,
            'brand': '',
        }
        # POSTメソッド実行
        res = self.client.post(VEHICLES_URL, payload)
        # POSTメソッドの結果がエラーになる事を確認する。（HTTPステータスが400が返ってくる事を確認する）
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # **************************************************************
    # segmentが空白の場合はエラーになる事を確認する
    def test_4_5_should_not_create_vehicle_with_invalid(self):
        # brandにテスト用のデータを登録しておく
        brand = create_brand(brand_name='Tesla')
        # 新規登録するデータ
        payload = {
            'vehicle_name': 'MODEL S',
            'release_year': 2019,
            'price': 500.00,
            'segment': '',
            'brand': brand.id,
        }
        # POSTメソッド実行
        res = self.client.post(VEHICLES_URL, payload)
        # POSTメソッドの結果がエラーになる事を確認する。（HTTPステータスが400が返ってくる事を確認する）
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # **************************************************************
    # patchで更新できる事を確認する
    def test_4_6_should_partial_update_vehicle(self):
        # segmentとbrandにテスト用のデータを登録しておく
        segment = create_segment(segment_name='Sedan')
        brand = create_brand(brand_name='Tesla')
        # １件登録しておく
        vehicle = create_vehicle(user=self.user, segment=segment, brand=brand)
        # 更新用のデータ設定
        payload = {'vehicle_name': 'MODEL X'}
        # URL生成する
        url = detail_vehicle_url(vehicle.id)
        # PATCHメソッド実行
        self.client.patch(url, payload)
        # 更新後のデータベースの内容を取得する
        vehicle.refresh_from_db()
        # 更新後のvehicle_nameの値が変わっている事を確認する
        self.assertEqual(vehicle.vehicle_name, payload['vehicle_name'])

    # **************************************************************
    # putで更新できる事を確認する
    def test_4_7_should_update_vehicle(self):
        # segmentとbrandにテスト用のデータを登録しておく
        segment = create_segment(segment_name='Sedan')
        brand = create_brand(brand_name='Tesla')
        # １件登録しておく
        vehicle = create_vehicle(user=self.user, segment=segment, brand=brand)
        # 更新用のデータ設定
        payload = {
            'vehicle_name': 'MODEL X',
            'release_year': 2019,
            'price': 600.00,
            'segment': segment.id,
            'brand': brand.id,
        }
        # URL生成する
        url = detail_vehicle_url(vehicle.id)
        # 変更前のモデル名の確認
        self.assertEqual(vehicle.vehicle_name, 'MODEL S')
        # PUTメソッド実行
        self.client.put(url, payload)
        # 更新後のデータベースの内容を取得する
        vehicle.refresh_from_db()
        # vehicle_nameの値が変わっている事を確認する
        self.assertEqual(vehicle.vehicle_name, payload['vehicle_name'])

    # **************************************************************
    # deleteで削除できる事を確認する
    def test_4_8_should_delete_vehicle(self):
        # segmentとbrandにテスト用のデータを登録しておく
        segment = create_segment(segment_name='Sedan')
        brand = create_brand(brand_name='Tesla')
        # １件登録しておく
        vehicle = create_vehicle(user=self.user, segment=segment, brand=brand)
        # 削除前は登録件数が１件ある事を確認する。
        self.assertEqual(1, Vehicle.objects.count())
        # URL生成する
        url = detail_vehicle_url(vehicle.id)
        # DELETEメソッド実行
        self.client.delete(url)
        # 削除後は登録件数が０件となっている事を確認する、
        self.assertEqual(0, Vehicle.objects.count())
        
    # **************************************************************
    # segmentの削除に連動して、vehicleも削除される事を確認する
    def test_4_9_should_cascade_delete_vehicle_by_segment_delete(self):
        # segmentとbrandにテスト用のデータを登録しておく
        segment = create_segment(segment_name='Sedan')
        brand = create_brand(brand_name='Tesla')
        create_vehicle(user=self.user, segment=segment, brand=brand)
        # segment削除前はVehicleの登録件数が１件ある事を確認する。
        self.assertEqual(1, Vehicle.objects.count())
        # URL生成する（segmentの削除）
        url = detail_seg_url(segment.id)
        # DELETEメソッド実行（segment）
        self.client.delete(url)
        # segment削除前はVehicleの登録件数が０件になる事を確認する。
        self.assertEqual(0, Vehicle.objects.count())

    # **************************************************************
    # brandの削除に連動して、vehicleも削除される事を確認する
    def test_4__10_should_cascade_delete_vehicle_by_brand_delete(self):
        # segmentとbrandにテスト用のデータを登録しておく
        segment = create_segment(segment_name='Sedan')
        brand = create_brand(brand_name='Tesla')
        create_vehicle(user=self.user, segment=segment, brand=brand)
        # brand削除前はVehicleの登録件数が１件ある事を確認する。
        self.assertEqual(1, Vehicle.objects.count())
        # URL生成する（brandの削除）
        url = detail_brand_url(brand.id)
        # DELETEメソッド実行（brand）
        self.client.delete(url)
        # brand削除前はVehicleの登録件数が０件になる事を確認する。
        self.assertEqual(0, Vehicle.objects.count())

## ==================================================================
## ログイン認証を行っていない場合にエラーになる事を確認する
## ==================================================================
class UnauthorizedVehicleApiTests(TestCase):

    # 認証が必要ないのでclientのみを定義する
    def setUp(self):
        self.client = APIClient()

    # **************************************************************
    # ログインしていない状態でGETメソッドがエラーになることを確認する
    def test_4__11_should_not_get_vehicles_when_unauthorized(self):
        # GETメソッド実行
        res = self.client.get(VEHICLES_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)



