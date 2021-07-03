from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

# テストするURIを定義する
CREATE_USER_URL = '/api/create/'
PROFILE_URL = '/api/profile/'
TOKEN_URL = '/api/auth/'

## ==================================================================
## トークン認証を通った後のテスト
## ==================================================================
class AuthorizedUserApiTests(TestCase):
    # 各テストの最初に処理されるため、必要
    # 認証用のユーザ作成
    def setUp(self):
        # テスト用ユーザ作成
        self.user = get_user_model().objects.create_user(username='dummy', password='dummy_pw')
        self.client = APIClient()
        # ダミーのユーザ情報でテストを実施するためのログイン
        self.client.force_authenticate(user=self.user)

    #テストケース1 ユーザ情報を取得できることを確認
    def test_1_1_should_get_user_profile(self):
        # GETメソッド実行
        res = self.client.get(PROFILE_URL)
        # GETメソッドの結果が成功した事を確認する（HTTPステータスが200が返ってくる事を確認する）
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # ユーザが一致していることを確認する
        self.assertEqual(res.data, {
            'id': self.user.id,
            'username': self.user.username,
        })

    #テストケース２ PUTでのアクセスがエラーになる事を確認する
    def test_1_2_should_not_allowed_by_PUT(self):
        # ログイン用のユーザ情報
        payload = {
            'username': 'dummy',
            'password': 'dummy_pw',
        }
        # PUTメソッド実行
        res = self.client.put(PROFILE_URL, payload)
        # PUTメソッドの結果がエラーになった事を確認する（HTTPステータスが405が返ってくる事を確認する）
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    # テストケース３ PATCHでのアクセスがエラーになる事を確認する
    def test_1_3_should_not_allowed_by_PATCH(self):
        # ログインするユーザ情報
        payload = {
            'username': 'dummy',
            'password': 'dummy_pw',
        }
        # PATCHメソッド実行
        res = self.client.patch(PROFILE_URL, payload)
        # PATCHメソッドの結果がエラーになった事を確認する（HTTPステータスが405が返ってくる事を確認する）
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

## ==================================================================
## ログイン認証が通っていない場合のテスト
## ==================================================================
class UnauthorizedUserApiTests(TestCase):

    # 認証が必要ないのでclientのみを定義する
    def setUp(self):
        self.client = APIClient()

    # ユーザが作成される事を確認する
    def test_1_4_should_create_new_user(self):
        # 新規作成するユーザ情報
        payload = {
            'username': 'dummy',
            'password': 'dummy_pw',
        }
        # POSTメソッド実行（ユーザ登録）
        res = self.client.post(CREATE_USER_URL, payload)
        # 成功している事を確認する（HTTPステータスが201が返ってくる事を確認する）
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        # ユーザ情報を取得する
        user = get_user_model().objects.get(username=payload['username'])
        # パスワードが一致する事を確認する。（パスワードはハッシュ化されているため、check_passwordを使用する）
        self.assertTrue(
            user.check_password(payload['password'])
        )
        # パスワードの項目がない事を確認する。
        self.assertNotIn('password', res.data)

    # 同じユーザ名でユーザ登録するとエラーになる事を確認する
    def test_1_5_should_not_create_user_by_same_credentials(self):
        # 新規作成するユーザ情報
        payload = {
            'username': 'dummy',
            'password': 'dummy_pw'
        }
        # テスト用にユーザ登録しておく（payloadは辞書型であるため、**をつける）
        get_user_model().objects.create_user(**payload)
        # POSTメソッド実行（ユーザ登録）
        res = self.client.post(CREATE_USER_URL, payload)
        #　エラーになる事を確認する。（HTTPステータスが400が返ってくる事を確認する）
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # パスワードが５文字未満の時はエラーになる事を確認する
    def test_1_6_should_not_create_user_with_short_pw(self):
        payload = {
            'username': 'dummy',
            'password': 'pw12'
        }
        # POSTメソッド実行（ユーザ登録）
        res = self.client.post(CREATE_USER_URL, payload)
        # エラーになる事を確認する。（HTTPステータスが400が返ってくる事を確認する）
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # トークンを取得できる事を確認する
    def test_1_7_should_response_token(self):
        payload = {
            'username': 'dummy',
            'password': 'dummy_pw'
        }
        # ユーザ登録を行う
        get_user_model().objects.create_user(**payload)
        # POSTメソッド実行（トークン作成）
        res = self.client.post(TOKEN_URL, payload)

        # レスポンスにトークンのフィールドが存在している事を確認する
        self.assertIn('token', res.data)
        # 成功した事を確認する（HTTPステータスが200が返ってくる事を確認する）
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    # パスワードが一致しないユーザはトークン作成でエラーになる事を確認する
    def test_1_8_should_not_response_token_with_invalid_credentials(self):
        # ユーザ登録を行う
        get_user_model().objects.create_user(username='dummy', password='dummy_pw')
        # ログイン用のユーザ、パスワード
        payload = {'username': 'dummy', 'password': 'wrong'}
        # POSTメソッド実行（トークン作成）
        res = self.client.post(TOKEN_URL, payload)

        # レスポンスにトークンのフィールドが存在していない事を確認する
        self.assertNotIn('token', res.data)
        # エラーになる事を確認する。（HTTPステータスが400が返ってくる事を確認する）
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # 存在しないユーザでトークン作成でエラーになる事を確認する
    def test_1_9_should_not_response_token_with_non_exist_credentials(self):
        # 存在しないユーザを定義する
        payload = {'username': 'dummy', 'password': 'dummy_pw'}
        # POSTメソッド実行（トークン作成）
        res = self.client.post(TOKEN_URL, payload)

        # レスポンスにトークンのフィールドが存在していない事を確認する
        self.assertNotIn('token', res.data)
        # エラーになる事を確認する。（HTTPステータスが400が返ってくる事を確認する）
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # パスワードが空白の場合は、トークン作成でエラーになる事を確認する
    def test_1__10_should_not_response_token_with_missing_field(self):
        # パスワードが空の状態のユーザを定義する
        payload = {'username': 'dummy', 'password': ''}
        # POSTメソッド実行（トークン作成）
        res = self.client.post(TOKEN_URL, payload)
        # レスポンスにトークンのフィールドが存在していない事を確認する
        self.assertNotIn('token', res.data)
        # エラーになる事を確認する。（HTTPステータスが400が返ってくる事を確認する）
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # ユーザ、パスワードが空白の場合は、トークン作成でエラーになる事を確認する
    def test_1__11_should_not_response_token_with_missing_field(self):
        # ユーザ、パスワードが空白のユーザを定義する
        payload = {'username': '', 'password': ''}
        # POSTメソッド実行（トークン作成）
        res = self.client.post(TOKEN_URL, payload)
        # レスポンスにトークンのフィールドが存在していない事を確認する
        self.assertNotIn('token', res.data)
        # エラーになる事を確認する。（HTTPステータスが400が返ってくる事を確認する）
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # トークンなしで、プロフィールの取得時にエラーになる
    def test_1__12_should_not_get_user_profile_when_unauthorized(self):
        # GETメソッド実行（プロフィール取得）
        res = self.client.get(PROFILE_URL)
        # エラーになる事を確認する。（HTTPステータスが401が返ってくる事を確認する）
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        
        

