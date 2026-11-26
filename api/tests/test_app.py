import threading
import unittest
from http.server import HTTPServer
from urllib.error import HTTPError
from urllib.request import urlopen

from api.app import APIHandler


class APITestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), APIHandler)

        cls.thread = threading.Thread(
            target=cls.server.serve_forever,
            daemon=True
        )

        cls.thread.start()

        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def test_health_endpoint(self):
        with urlopen(f"{self.base_url}/health") as response:
            self.assertEqual(response.status, 200)
            self.assertEqual(
                response.headers.get_content_type(),
                "application/json"
            )
            self.assertEqual(
                response.read().decode(),
                '{"status": "healthy"}'
            )

    def test_home_endpoint(self):
        with urlopen(f"{self.base_url}/") as response:
            self.assertEqual(response.status, 200)
            self.assertEqual(
                response.read().decode(),
                "Hello from Docker!"
            )

    def test_unknown_endpoint(self):
        with self.assertRaises(HTTPError) as error:
            urlopen(f"{self.base_url}/missing")

        self.assertEqual(error.exception.code, 404)


if __name__ == "__main__":
    unittest.main()
