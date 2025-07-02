import unittest
from app import create_app
from models import User, db
from config import TestConfig

class TestEmailVerification(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Create test database
        db.create_all()
        
        # Add test user
        self.test_user = User(
            username='testuser',
            email='kelompok7cc2025@gmail.com',
            password='testpass',
            email_verified=False
        )
        db.session.add(self.test_user)
        db.session.commit()

    def test_token_generation_and_verification(self):
        # Generate token
        token = self.test_user.generate_email_token()
        
        # Verify token
        verified_user = User.verify_email_token(token)
        
        self.assertIsNotNone(verified_user)
        self.assertEqual(verified_user.id, self.test_user.id)
        self.assertEqual(verified_user.email, self.test_user.email)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

if __name__ == '__main__':
    unittest.main()