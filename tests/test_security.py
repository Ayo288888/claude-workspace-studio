import unittest
from security import SessionKeyManager, mask_api_key, validate_anthropic_key

class TestSecurity(unittest.TestCase):
    def test_encryption_decryption_roundtrip(self):
        manager = SessionKeyManager()
        raw_key = "sk-ant-api03-testkey-1234567890abcdefghijklmnopqrstuvwxyz"
        encrypted = manager.encrypt_key(raw_key)
        self.assertNotEqual(raw_key, encrypted)
        decrypted = manager.decrypt_key(encrypted)
        self.assertEqual(raw_key, decrypted)

    def test_mask_api_key(self):
        raw_key = "sk-ant-api03-1234567890abcdef-secret"
        masked = mask_api_key(raw_key)
        self.assertTrue(masked.startswith("sk-ant-"))
        self.assertTrue(masked.endswith("cret"))
        self.assertIn("••••", masked)
        self.assertNotIn("1234567890abcdef", masked)

    def test_validate_anthropic_key(self):
        self.assertTrue(validate_anthropic_key("sk-ant-api03-abcdef1234567890abcdef"))
        self.assertFalse(validate_anthropic_key("invalid-key"))
        self.assertFalse(validate_anthropic_key(""))
        self.assertFalse(validate_anthropic_key(None))

if __name__ == "__main__":
    unittest.main()
