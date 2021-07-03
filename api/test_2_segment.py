from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
# Segmentのモデルとシリアライザー
from .models import Segment
from .serializers import SegmentSerializer

SEGMENTS_URL = '/api/segments/'

# セグメントを作成するための関数
def create_segment(segment_name):
    return Segment.objects.create(segment_name=segment_name)

# キーを含むURLを作成する　（reverseはURLのパスを生成する）
def detail_url(segment_id):
    return reverse('api:segment-detail', args=[segment_id])

## ==================================================================
## トークンの認証を通ったユーザでテストする
## ==================================================================
class AuthorizedSegmentApiTests(TestCase):
    # 各テストの最初に処理されるため、必要
    # 認証用のユーザ作成
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='dummy', password='dummy_pw')
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    # **************************************************************
    # GETメソッドでデータが取得できる事を確認する。
    def test_2_1_should_get_all_segments(self):
        # SegmentにSUVとSedanのレコード追加
        create_segment(segment_name="SUV")
        create_segment(segment_name="Sedan")
        # GETメソッド実行
        res = self.client.get(SEGMENTS_URL)
        # Segmentの全データを取得する
        segments = Segment.objects.all().order_by('id')
        # Segmentをシリアライザーを通した後のデータにする。（many=Trueは複数レコードの場合に指定する）
        serializer = SegmentSerializer(segments, many=True)
        # GETメソッドの結果が成功した事を確認する（HTTPステータスが200が返ってくる事を確認する）
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # 取得結果とセグメントのデータが一致するか確認する
        self.assertEqual(res.data, serializer.data)

    # **************************************************************
    # ID指定で１件だけ取得できる事を確認する
    def test_2_2_should_get_single_segment(self):
        # SegmentにSUVのレコード追加
        segment = create_segment(segment_name="SUV")
        #　データ取得用のURLを設定する
        url = detail_url(segment.id)
        # GETメソッド実行
        res = self.client.get(url)
        # segmentをシリアライザーを通した後のデータにする。
        serializer = SegmentSerializer(segment)
        # GETメソッドの取得結果と登録したデータが一致するか確認する
        self.assertEqual(res.data, serializer.data)

    # **************************************************************
    # 新規登録できる事を確認する
    def test_2_3_should_create_new_segment_successfully(self):
        # 新規登録するデータ
        payload = {'segment_name': 'K-Car'}
        # POSTメソッド実行
        res = self.client.post(SEGMENTS_URL, payload)
        # POSTメソッドの結果が成功した事を確認する（HTTPステータスが201が返ってくる事を確認する）
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        # データベースから名前で検索し、exists()を指定する事で存在している場合はTrueとなる
        exists = Segment.objects.filter(
            segment_name=payload['segment_name']
        ).exists()
        # データが存在している場合はexistsにTrueが設定されているため、Trueだと正常
        self.assertTrue(exists)

    # **************************************************************
    # segment_nameが空白の場合はエラーになる事を確認する
    def test_2_4_should_not_create_new_segment_with_invalid(self):
        # 新規作成するデータ
        payload = {'segment_name': ''}
        # POSTメソッド実行
        res = self.client.post(SEGMENTS_URL, payload)
        # POSTメソッドの結果がエラーになる事を確認する。（HTTPステータスが400が返ってくる事を確認する）
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # **************************************************************
    # patchで更新できる事を確認する
    def test_2_5_should_partial_update_segment(self):
        # １件登録しておく
        segment = create_segment(segment_name="SUV")
        # 更新用のデータ設定
        payload = {'segment_name': 'Compact SUV'}
        # URL生成する
        url = detail_url(segment.id)
        # PATCHメソッド実行
        self.client.patch(url, payload)
        # 更新後のデータベースの内容を取得する
        segment.refresh_from_db()
        # segment_nameの値が変わっている事を確認する
        self.assertEqual(segment.segment_name, payload['segment_name'])

    # **************************************************************
    # putで更新できる事を確認する
    def test_2_6_should_update_segment(self):
        # １件登録しておく
        segment = create_segment(segment_name="SUV")
        # 更新用のデータ設定
        payload = {'segment_name': 'Compact SUV'}
        url = detail_url(segment.id)
        # PUTメソッド実行
        self.client.put(url, payload)
        # 更新後のデータベースの内容を取得する
        segment.refresh_from_db()
        # segment_nameの値が変わっている事を確認する
        self.assertEqual(segment.segment_name, payload['segment_name'])

    # **************************************************************
    # deleteで削除できる事を確認する
    def test_2_7_should_delete_segment(self):
        # １件登録しておく
        segment = create_segment(segment_name="SUV")
        # 登録件数が１件であることを確認する
        self.assertEqual(1, Segment.objects.count())
        # URL生成する
        url = detail_url(segment.id)
        # DELETEメソッド実行
        self.client.delete(url)
        # 登録件数が０件であることを確認する
        self.assertEqual(0, Segment.objects.count())

## ==================================================================
## ログイン認証を行っていない場合にエラーになる事を確認する
## ==================================================================
class UnauthorizedSegmentApiTests(TestCase):

    # 認証が必要ないのでclientのみを定義する
    def setUp(self):
        self.client = APIClient()

    # **************************************************************
    # ログインしていない状態でGETメソッドがエラーになることを確認する
    def test_2_8_should_not_get_segments_when_unauthorized(self):
        # GETメソッド実行
        res = self.client.get(SEGMENTS_URL)
        # GETメソッドの結果がエラーになる事を確認する。（HTTPステータスが401が返ってくる事を確認する）
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    # **************************************************************
    # ログインしていない状態でPOSTメソッドがエラーになることを確認する
    def test_2_9_should_not_post_segments_when_unauthorized(self):
        # 新規作成するデータ
        payload = {'segment_name': 'K-Car'}
        # POSTメソッド実行
        res = self.client.post(SEGMENTS_URL,payload)
        # POSTメソッドの結果がエラーになる事を確認する。（HTTPステータスが401が返ってくる事を確認する）
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    # **************************************************************
    # ログインしていない状態でPOSTメソッドがエラーになることを確認する
    def test_2__10_should_not_put_segments_when_unauthorized(self):
        # １件登録しておく
        create_segment(segment_name="SUV")
        # 更新するデータ
        payload = {'segment_name': 'K-Car'}
        # URL生成する
        url = detail_url(1)
        # PUTメソッド実行
        res = self.client.put(url,payload)
        # PUTメソッドの結果がエラーになる事を確認する。（HTTPステータスが401が返ってくる事を確認する）
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    # **************************************************************
    # ログインしていない状態でPATCHメソッドがエラーになることを確認する
    def test_2__11_should_not_patch_segments_when_unauthorized(self):
        # １件登録しておく
        create_segment(segment_name="SUV")
        # 更新するデータ
        payload = {'segment_name': 'K-Car'}
        # URL生成する
        url = detail_url(1)
        # PATCHメソッド実行
        res = self.client.patch(url, payload)
        # PUTメソッドの結果がエラーになる事を確認する。（HTTPステータスが401が返ってくる事を確認する）
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    # **************************************************************
    # ログインしていない状態でDELETEメソッドがエラーになることを確認する
    def test_2__12_should_not_delete_segments_when_unauthorized(self):
        # URL生成する
        url = detail_url(1)
        # DELETEメソッド実行
        res = self.client.delete(url)
        # DELETEメソッドの結果がエラーになる事を確認する。（HTTPステータスが401が返ってくる事を確認する）
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        