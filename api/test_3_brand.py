from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
# Brandのモデルとシリアライザー
from .models import Brand
from .serializers import BrandSerializer

BRANDS_URL = '/api/brands/'

# ブランドを作成するための関数
def create_brand(brand_name):
    return Brand.objects.create(brand_name=brand_name)

# キーを含むURLを作成する　（reverseはURLのパスを生成する）
def detail_url(brand_id):
    return reverse('api:brand-detail', args=[brand_id])

# トークンの認証を通ったユーザでテストする
class AuthorizedBrandApiTests(TestCase):
    # 各テストの最初に処理されるため、必要
    # 認証用のユーザ作成
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='dummy', password='dummy_pw')
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    # GETメソッドでデータが取得できる事を確認する。
    def test_3_1_should_get_brands(self):
        # BrandにToyotaとTeslaのレコード追加
        create_brand(brand_name="Toyota")
        create_brand(brand_name="Tesla")
        # GETメソッド実行
        res = self.client.get(BRANDS_URL)
        # Brandの全データを取得する
        brands = Brand.objects.all().order_by('id')
        # Brandをシリアライザーを通した後のデータにする。（many=Trueは複数レコードの場合に指定する）
        serializer = BrandSerializer(brands, many=True)
        # GETメソッドの結果が成功した事を確認する（HTTPステータスが200が返ってくる事を確認する）
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # 取得結果とセグメントのデータが一致するか確認する
        self.assertEqual(res.data, serializer.data)

    # ID指定で１件だけ取得できる事を確認する
    def test_3_2_should_get_single_brand(self):
        # BrandにToyotaのレコード追加
        brand = create_brand(brand_name="Toyota")
        # データ取得用のURLを設定する
        url = detail_url(brand.id)
        # GETメソッド実行
        res = self.client.get(url)
        # Brandをシリアライザーを通した後のデータにする。
        serializer = BrandSerializer(brand)
        # GETメソッドの結果が成功した事を確認する（HTTPステータスが200が返ってくる事を確認する）
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # GETメソッドの取得結果と登録したデータが一致するか確認する
        self.assertEqual(res.data, serializer.data)

    # 新規登録できる事を確認する
    def test_3_3_should_create_new_brand_successfully(self):
        # 新規登録するデータ
        payload = {'brand_name': 'Audi'}
        # POSTメソッド実行
        res = self.client.post(BRANDS_URL, payload)
        # データベースから名前で検索し、exists()を指定する事で存在している場合はTrueとなる
        exists = Brand.objects.filter(
            brand_name=payload['brand_name']
        ).exists()
        # POSTメソッドの結果が成功した事を確認する（HTTPステータスが201が返ってくる事を確認する）
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        # データが存在している場合はexistsにTrueが設定されているため、Trueだと正常
        self.assertTrue(exists)

    # brand_nameが空白の場合はエラーになる事を確認する
    def test_3_4_should_not_create_brand_with_invalid(self):
        # 新規作成するデータ
        payload = {'brand_name': ''}
        # POSTメソッド実行
        res = self.client.post(BRANDS_URL, payload)
        # POSTメソッドの結果がエラーになる事を確認する。（HTTPステータスが400が返ってくる事を確認する）
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # patchで更新できる事を確認する
    def test_3_5_should_partial_update_brand(self):
        # １件登録しておく
        brand = create_brand(brand_name="Toyota")
        # 更新用のデータ設定
        payload = {'brand_name': 'Lexus'}
        # URL生成する
        url = detail_url(brand.id)
        # PATCHメソッド実行
        self.client.patch(url, payload)
        # 更新後のデータベースの内容を取得する
        brand.refresh_from_db()
        # 更新後のbrand_nameの値が変わっている事を確認する
        self.assertEqual(brand.brand_name, payload['brand_name'])

    # putで更新できる事を確認する
    def test_3_6_should_update_brand(self):
        # １件登録しておく
        brand = create_brand(brand_name="Toyota")
        # 更新用のデータ設定
        payload = {'brand_name': 'Lexus'}
        # URL生成する
        url = detail_url(brand.id)
        # PUTメソッド実行
        self.client.put(url, payload)
        # 更新後のデータベースの内容を取得する
        brand.refresh_from_db()
        # brand_nameの値が変わっている事を確認する
        self.assertEqual(brand.brand_name, payload['brand_name'])

    # deleteで削除できる事を確認する
    def test_3_7_should_delete_brand(self):
        brand = create_brand(brand_name="Toyota")
        # 登録件数が１件であることを確認する
        self.assertEqual(1, Brand.objects.count())
        # URL生成する
        url = detail_url(brand.id)
        # DELETEメソッド実行
        self.client.delete(url)
        # 登録件数が０件であることを確認する
        self.assertEqual(0, Brand.objects.count())

#　ログイン認証を行っていない場合にエラーになる事を確認する
class UnauthorizedBrandApiTests(TestCase):

    # 認証が必要ないのでclientのみを定義する
    def setUp(self):
        self.client = APIClient()

    # ログインしていない状態でGETメソッドがエラーになることを確認する
    def test_3_8_should_not_get_brands_when_unauthorized(self):
        # GETメソッド実行
        res = self.client.get(BRANDS_URL)
        # GETメソッドの結果がエラーになる事を確認する。（HTTPステータスが401が返ってくる事を確認する）
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    # ログインしていない状態でPOSTメソッドがエラーになることを確認する
    def test_3_9_should_not_post_brands_when_unauthorized(self):
        # 新規作成するデータ
        payload = {'brand_name': 'Toyota'}
        # POSTメソッド実行
        res = self.client.post(BRANDS_URL,payload)
        # POSTメソッドの結果がエラーになる事を確認する。（HTTPステータスが401が返ってくる事を確認する）
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    # ログインしていない状態でPOSTメソッドがエラーになることを確認する
    def test_3__10_should_not_put_brands_when_unauthorized(self):
        # 新規作成するデータ
        payload = {'brand_name': 'Toyota'}
        # URL生成する
        url = detail_url(1)
        # PUTメソッド実行
        res = self.client.put(url,payload)
        # PUTメソッドの結果がエラーになる事を確認する。（HTTPステータスが401が返ってくる事を確認する）
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    # ログインしていない状態でPOSTメソッドがエラーになることを確認する
    def test_3__11_should_not_delete_brands_when_unauthorized(self):
        # URL生成する
        url = detail_url(1)
        # DELETEメソッド実行
        res = self.client.delete(url)
        # DELETEメソッドの結果がエラーになる事を確認する。（HTTPステータスが401が返ってくる事を確認する）
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)