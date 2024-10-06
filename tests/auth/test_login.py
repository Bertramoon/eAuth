from datetime import datetime, timedelta
import unittest

from eAuth import create_app, verify_token, SecurityLog
from eAuth.extensions import db, limiter
from eAuth.models import User


class TestLogin(unittest.TestCase):
    app = None
    context = None
    login_url = "/api/auth/login"
    limiter.enabled = False

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = create_app('test')
        cls.app.config["TESTING"] = True
        cls.app.config["SQLALCHEMY_ECHO"] = False
        cls.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        cls.context = cls.app.test_request_context()
        cls.context.push()
        cls.client = cls.app.test_client()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.context.pop()

    def setUp(self) -> None:
        db.create_all()

    def tearDown(self) -> None:
        db.drop_all()

    def test_common_login(self):
        """正常登录"""
        user = self.get_common_user()
        data = {
            "username": user["username"],
            "password": user["password"]
        }
        res = self.client.post(self.login_url, json=data)
        result = res.json
        self.assertTrue(result.get("success"))
        self.assertIn("token", result)
        token = result["token"]
        verify_user = verify_token(token)
        self.assertIsNotNone(verify_user)
        self.assertEqual(verify_user.username, user["username"])
        self.assertTrue(verify_user.validate_password(data["password"]))

    def test_wrong_password(self):
        """账号或密码错误时的登录"""
        user = self.get_common_user()
        data = {
            "username": user["username"],
            "password": "hack"
        }
        res = self.client.post(self.login_url, json=data)
        result = res.json
        self.assertFalse(result.get("success"))

    def test_locked(self):
        """登录被锁用户"""
        user = self.get_locked_user()
        data = {
            "username": user["username"],
            "password": user["password"]
        }
        res = self.client.post(self.login_url, json=data)
        result = res.json
        self.assertFalse(result.get("success"))

    def test_login_incorrect(self):
        """登录失败被锁定用户时无法登录"""
        user = self.get_login_incorrect_user()
        data = {
            "username": user["username"],
            "password": user["password"]
        }
        res = self.client.post(self.login_url, json=data)
        result = res.json
        self.assertFalse(result.get("success"))

    def test_short_login_incorrect(self):
        """登录失败被暂时锁定用户时无法登录"""
        user = self.get_short_login_incorrect_user()
        data = {
            "username": user["username"],
            "password": user["password"]
        }
        res = self.client.post(self.login_url, json=data)
        result = res.json
        self.assertTrue(result.get("success"))

        data.update({"password": "fake_password"})
        for _ in range(self.app.config.get("SHORT_MAX_LOGIN_INCORRECT")):
            self.client.post(self.login_url, json=data)
        data.update({"password": user["password"]})
        res = self.client.post(self.login_url, json=data)
        result = res.json
        self.assertFalse(result.get("success"), msg="登录失败超过配置的次数后应被暂时锁定，无法登录")

    def test_will_short_login_incorrect(self):
        """登录失败n-1次时再使用正确密码登录"""
        user = self.get_admin_user()
        data = {
            "username": user["username"],
            "password": "fake_password"
        }

        for _ in range(self.app.config.get("SHORT_MAX_LOGIN_INCORRECT") - 1):
            res = self.client.post(self.login_url, json=data)
            self.assertFalse(res.json.get("success"), msg="密码错误时不应该能够登录")

        data.update({'password': user["password"]})
        res = self.client.post(self.login_url, json=data)
        result = res.json
        self.assertTrue(result.get("success"))

    def test_empty_username(self):
        """空用户名登录"""
        res = self.client.post(self.login_url, json={"password": "123456"})
        result = res.json
        self.assertFalse(result.get("success"))

    def test_empty_password(self):
        """空密码登录"""
        res = self.client.post(self.login_url, json={"username": "123456"})
        result = res.json
        self.assertFalse(result.get("success"))

    def get_common_user(self):
        user = {
            "username": "user",
            "password": "123456"
        }
        self.set_user(**user)
        return user

    def get_admin_user(self):
        user = {
            "username": "admin",
            "password": "123456"
        }
        self.set_user(**user)
        return user

    def get_locked_user(self):
        user = {
            "username": "locked",
            "password": "123456",
            "locked": True
        }
        self.set_user(**user)
        return user

    def get_login_incorrect_user(self):
        user = {
            "username": "locked",
            "password": "123456",
            "locked": False,
            "login_incorrect": self.app.config.get("MAX_LOGIN_INCORRECT", 50)
        }
        self.set_user(**user)
        return user

    def get_short_login_incorrect_user(self):
        user = {
            "username": "locked",
            "password": "123456",
            "locked": False,
            "login_incorrect": self.app.config.get("SHORT_MAX_LOGIN_INCORRECT")
        }
        self.set_user(**user)
        security_log = SecurityLog(username=user['username'], ip_addr='127.0.0.1', operate='登录', success=False,
                                   operate_datetime=datetime.utcnow() - timedelta(
                                       hours=self.app.config.get("SHORT_MAX_LOGIN_DELAY")))
        db.session.add(security_log)
        db.session.commit()
        return user

    @staticmethod
    def set_user(username, password, **kwargs):
        user = User(
            username=username,
            **kwargs
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()


if __name__ == '__main__':
    unittest.main()
