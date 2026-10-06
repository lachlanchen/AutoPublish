import unittest

from scripts.diagnose_douyin_upload import public_response


class ResponseSummaryTests(unittest.TestCase):
    def test_excludes_credentials_and_upload_identifiers(self):
        response = {"ResponseMetadata": {"RequestId": "private", "Error": {
            "Code": "UploadFailed", "Message": "retry https://example.test/?signature=secret",
        }}, "UploadId": "private", "Authorization": "secret", "Cookies": {"code": "secret"}}
        self.assertEqual(public_response(response), {"ResponseMetadata": {"Error": {
            "Code": "UploadFailed", "Message": "retry [url]",
        }}})

    def test_only_json_status_summary_is_returned(self):
        self.assertEqual(public_response(["private"]), {})
        self.assertEqual(public_response({"data": {"status": "success", "url": "private"}}),
                         {"data": {"status": "success"}})


if __name__ == "__main__":
    unittest.main()
