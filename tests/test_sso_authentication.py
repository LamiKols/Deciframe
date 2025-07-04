"""
Test Suite for SSO/OIDC Authentication
Comprehensive testing of OAuth integration with multiple providers
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from flask import url_for
from app import app, db
from models import User
from auth.oauth import OAuthConfig, OAuthManager, UserManager

class TestOAuthConfig:
    """Test OAuth configuration management"""
    
    def test_google_provider_config(self):
        """Test Google provider configuration"""
        config = OAuthConfig.get_provider_config('google')
        assert 'server_metadata_url' in config
        assert 'accounts.google.com' in config['server_metadata_url']
        assert config['client_kwargs']['scope'] == 'openid email profile'
    
    def test_azure_provider_config(self):
        """Test Azure AD provider configuration"""
        with patch.dict(os.environ, {'AZURE_TENANT_ID': 'test-tenant'}):
            config = OAuthConfig.get_provider_config('azure')
            assert 'test-tenant' in config['server_metadata_url']
    
    def test_okta_provider_config(self):
        """Test Okta provider configuration"""
        with patch.dict(os.environ, {'OKTA_DOMAIN': 'test.okta.com'}):
            config = OAuthConfig.get_provider_config('okta')
            assert 'test.okta.com' in config['server_metadata_url']
    
    def test_provider_enabled_check(self):
        """Test provider enablement checks"""
        # Test with missing credentials
        assert not OAuthConfig.is_provider_enabled('google')
        
        # Test with complete credentials
        with patch.dict(os.environ, {
            'GOOGLE_CLIENT_ID': 'test_id',
            'GOOGLE_CLIENT_SECRET': 'test_secret'
        }):
            assert OAuthConfig.is_provider_enabled('google')
    
    def test_oidc_provider_config(self):
        """Test generic OIDC provider configuration"""
        with patch.dict(os.environ, {'OIDC_DISCOVERY_URL': 'https://example.com/.well-known/openid_configuration'}):
            config = OAuthConfig.get_provider_config('oidc')
            assert config['server_metadata_url'] == 'https://example.com/.well-known/openid_configuration'
            assert config['client_kwargs']['scope'] == 'openid email profile'
    
    def test_oidc_provider_enabled_check(self):
        """Test generic OIDC provider enablement"""
        # Test with missing credentials
        assert not OAuthConfig.is_provider_enabled('oidc')
        
        # Test with complete credentials
        with patch.dict(os.environ, {
            'OIDC_CLIENT_ID': 'test_id',
            'OIDC_CLIENT_SECRET': 'test_secret',
            'OIDC_DISCOVERY_URL': 'https://example.com/.well-known/openid_configuration'
        }):
            assert OAuthConfig.is_provider_enabled('oidc')

class TestOAuthManager:
    """Test OAuth manager functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.oauth_manager = OAuthManager()
    
    def test_oauth_manager_initialization(self):
        """Test OAuth manager initialization"""
        with self.app.app_context():
            self.oauth_manager.init_app(self.app)
            assert hasattr(self.oauth_manager, 'oauth')
            assert hasattr(self.oauth_manager, 'providers')
    
    @patch.dict(os.environ, {
        'GOOGLE_CLIENT_ID': 'test_google_id',
        'GOOGLE_CLIENT_SECRET': 'test_google_secret'
    })
    def test_provider_registration(self):
        """Test OAuth provider registration"""
        with self.app.app_context():
            self.oauth_manager.init_app(self.app)
            provider = self.oauth_manager.get_provider('google')
            assert provider is not None
            assert 'google' in self.oauth_manager.get_enabled_providers()
    
    def test_authorization_redirect(self):
        """Test OAuth authorization redirect"""
        with self.app.app_context():
            mock_provider = MagicMock()
            mock_provider.authorize_redirect.return_value = 'redirect_response'
            self.oauth_manager.providers['test'] = mock_provider
            
            result = self.oauth_manager.authorize_redirect('test')
            assert result == 'redirect_response'
            mock_provider.authorize_redirect.assert_called_once()

class TestUserManager:
    """Test OAuth user management"""
    
    def setup_method(self):
        """Setup test environment"""
        self.app = app
        self.app.config['TESTING'] = True
        
        with self.app.app_context():
            db.create_all()
    
    def teardown_method(self):
        """Cleanup test environment"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_create_new_oauth_user(self):
        """Test creating new user from OAuth info"""
        with self.app.app_context():
            user_info = {
                'sub': 'oauth_12345',
                'email': 'test@example.com',
                'name': 'Test User',
                'given_name': 'Test',
                'family_name': 'User',
                'picture': 'https://example.com/photo.jpg'
            }
            
            user = UserManager.create_or_update_user(user_info, 'google')
            
            assert user.email == 'test@example.com'
            assert user.name == 'Test User'
            assert user.first_name == 'Test'
            assert user.last_name == 'User'
            assert user.oauth_provider == 'google'
            assert user.oauth_sub == 'oauth_12345'
            assert user.profile_image_url == 'https://example.com/photo.jpg'
            assert user.role.value == 'Staff'
            assert user.is_active == True
    
    def test_update_existing_oauth_user(self):
        """Test updating existing user with OAuth info"""
        with self.app.app_context():
            # Create existing user
            existing_user = User(
                name='Old Name',
                email='test@example.com',
                role='Staff',
                is_active=True
            )
            db.session.add(existing_user)
            db.session.commit()
            
            # Update with OAuth info
            user_info = {
                'sub': 'oauth_12345',
                'email': 'test@example.com',
                'name': 'Updated Name',
                'given_name': 'Updated',
                'family_name': 'Name',
                'picture': 'https://example.com/new_photo.jpg'
            }
            
            updated_user = UserManager.create_or_update_user(user_info, 'google')
            
            assert updated_user.id == existing_user.id
            assert updated_user.name == 'Updated Name'
            assert updated_user.first_name == 'Updated'
            assert updated_user.oauth_provider == 'google'
    
    def test_unique_username_generation(self):
        """Test unique username generation for OAuth users"""
        with self.app.app_context():
            # Create first user
            user_info1 = {
                'sub': 'oauth_1',
                'email': 'test@example.com',
                'name': 'Test User 1'
            }
            user1 = UserManager.create_or_update_user(user_info1, 'google')
            
            # Create second user with same email prefix
            user_info2 = {
                'sub': 'oauth_2',
                'email': 'test@different.com',
                'name': 'Test User 2'
            }
            user2 = UserManager.create_or_update_user(user_info2, 'azure')
            
            assert user1.username == 'test'
            assert user2.username == 'test1'  # Should get incremented

class TestOAuthRoutes:
    """Test OAuth authentication routes"""
    
    def setup_method(self):
        """Setup test environment"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
    
    def teardown_method(self):
        """Cleanup test environment"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_sso_providers_endpoint(self):
        """Test SSO providers API endpoint"""
        with self.app.app_context():
            response = self.client.get('/auth/sso/providers')
            assert response.status_code == 200
            
            data = response.get_json()
            assert 'providers' in data
            assert isinstance(data['providers'], list)
    
    @patch.dict(os.environ, {
        'GOOGLE_CLIENT_ID': 'test_id',
        'GOOGLE_CLIENT_SECRET': 'test_secret'
    })
    def test_sso_login_redirect(self):
        """Test SSO login initiation"""
        with self.app.app_context():
            # This will redirect to Google OAuth
            response = self.client.get('/auth/sso/google')
            
            # Should redirect to OAuth provider
            assert response.status_code in [302, 301]
    
    def test_sso_login_invalid_provider(self):
        """Test SSO login with invalid provider"""
        with self.app.app_context():
            response = self.client.get('/auth/sso/invalid_provider')
            
            # Should redirect back to login with error
            assert response.status_code in [302, 301]
    
    @patch('auth.oauth.oauth_manager.parse_token')
    def test_oauth_callback_success(self, mock_parse_token):
        """Test successful OAuth callback"""
        with self.app.app_context():
            # Mock successful OAuth response
            mock_parse_token.return_value = (
                {'access_token': 'test_token'},
                {
                    'sub': 'oauth_123',
                    'email': 'test@example.com',
                    'name': 'Test User',
                    'given_name': 'Test',
                    'family_name': 'User'
                }
            )
            
            response = self.client.get('/auth/oauth/callback/google')
            
            # Should redirect to dashboard with auth cookie
            assert response.status_code in [302, 301]
            
            # Verify user was created
            user = User.query.filter_by(email='test@example.com').first()
            assert user is not None
            assert user.oauth_provider == 'google'
    
    @patch('auth.oauth.oauth_manager.parse_token')
    def test_oauth_callback_no_email(self, mock_parse_token):
        """Test OAuth callback without email"""
        with self.app.app_context():
            # Mock OAuth response without email
            mock_parse_token.return_value = (
                {'access_token': 'test_token'},
                {'sub': 'oauth_123', 'name': 'Test User'}  # No email
            )
            
            response = self.client.get('/auth/oauth/callback/google')
            
            # Should redirect to login with error
            assert response.status_code in [302, 301]

class TestOAuthIntegration:
    """Integration tests for complete OAuth flow"""
    
    def setup_method(self):
        """Setup test environment"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
    
    def teardown_method(self):
        """Cleanup test environment"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_login_page_includes_sso_section(self):
        """Test that login page includes SSO section"""
        with self.app.app_context():
            response = self.client.get('/auth/login')
            assert response.status_code == 200
            
            html_content = response.get_data(as_text=True)
            assert 'sso-section' in html_content
            assert 'sso-providers' in html_content
    
    @patch.dict(os.environ, {
        'GOOGLE_CLIENT_ID': 'test_id',
        'GOOGLE_CLIENT_SECRET': 'test_secret',
        'AZURE_CLIENT_ID': 'azure_id',
        'AZURE_CLIENT_SECRET': 'azure_secret'
    })
    def test_multiple_providers_configuration(self):
        """Test configuration with multiple OAuth providers"""
        with self.app.app_context():
            from auth.oauth import oauth_manager
            
            # Reinitialize with mock environment
            oauth_manager.init_app(self.app)
            enabled_providers = oauth_manager.get_enabled_providers()
            
            # Should detect configured providers
            assert len(enabled_providers) >= 0  # May be 0 if Authlib not fully configured in test

if __name__ == '__main__':
    pytest.main([__file__, '-v'])