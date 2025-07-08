# DeciFrame SSO/OIDC Authentication Setup Guide

## Overview
DeciFrame now supports enterprise Single Sign-On (SSO) and OpenID Connect (OIDC) authentication alongside traditional password-based authentication. This enables seamless integration with corporate identity providers.

## Supported Providers
- **Google Workspace** (OAuth 2.0 / OIDC)
- **Microsoft Azure AD** (OAuth 2.0 / OIDC)
- **Okta** (OIDC)
- **Auth0** (OIDC)
- **Generic OIDC** (Any OpenID Connect compliant provider)

## Environment Configuration

### Google Workspace Setup
```bash
# Required environment variables
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
```

**Configuration Steps:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Google+ API
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client IDs"
5. Set application type to "Web application"
6. Add authorized redirect URIs:
   - `https://yourdomain.com/auth/oauth/callback/google`
   - `http://localhost:5000/auth/oauth/callback/google` (for development)

### Microsoft Azure AD Setup
```bash
# Required environment variables
AZURE_CLIENT_ID=your_azure_application_id
AZURE_CLIENT_SECRET=your_azure_client_secret
AZURE_TENANT_ID=your_tenant_id  # Optional, defaults to "common"
```

**Configuration Steps:**
1. Go to [Azure Portal](https://portal.azure.com/)
2. Navigate to "Azure Active Directory" → "App registrations"
3. Click "New registration"
4. Set redirect URI: `https://yourdomain.com/auth/oauth/callback/azure`
5. Go to "Certificates & secrets" → "New client secret"
6. Note the Application (client) ID and client secret value

### Okta Setup
```bash
# Required environment variables
OKTA_CLIENT_ID=your_okta_client_id
OKTA_CLIENT_SECRET=your_okta_client_secret
OKTA_DOMAIN=your_okta_domain.okta.com
```

**Configuration Steps:**
1. Log in to your Okta admin console
2. Go to "Applications" → "Create App Integration"
3. Choose "OIDC - OpenID Connect" and "Web Application"
4. Set sign-in redirect URI: `https://yourdomain.com/auth/oauth/callback/okta`
5. Note the Client ID and Client Secret

### Auth0 Setup
```bash
# Required environment variables
AUTH0_CLIENT_ID=your_auth0_client_id
AUTH0_CLIENT_SECRET=your_auth0_client_secret
AUTH0_DOMAIN=your_tenant.auth0.com
```

**Configuration Steps:**
1. Log in to [Auth0 Dashboard](https://manage.auth0.com/)
2. Go to "Applications" → "Create Application"
3. Choose "Regular Web Applications"
4. Set allowed callback URLs: `https://yourdomain.com/auth/oauth/callback/auth0`
5. Note the Client ID and Client Secret from Settings

### Generic OIDC Setup
```bash
# Required environment variables
OIDC_CLIENT_ID=your_oidc_client_id
OIDC_CLIENT_SECRET=your_oidc_client_secret
OIDC_DISCOVERY_URL=https://accounts.example.com/.well-known/openid-configuration
OIDC_REDIRECT_URI=https://yourapp.com/auth/oauth/callback/oidc
```

**Configuration Steps:**
1. Configure your OpenID Connect compliant identity provider
2. Create a new application/client in your provider's console
3. Set the redirect URI to: `https://yourdomain.com/auth/oauth/callback/oidc`
4. Ensure the provider supports the OpenID Connect Discovery specification
5. Note the Client ID, Client Secret, and Discovery URL

**Supported OIDC Providers:**
- Keycloak
- Ping Identity
- ForgeRock
- Custom OIDC implementations
- Enterprise identity providers with OIDC support

## Features

### Automatic User Provisioning
- Users are automatically created on first SSO login
- Email addresses are used as unique identifiers
- Default role assignment (Staff) with admin promotion available
- Profile information synchronized from identity provider

### Hybrid Authentication
- Traditional email/password authentication remains available
- SSO options appear dynamically on login page when configured
- Seamless switching between authentication methods

### Security Features
- JWT-based stateless authentication
- Secure HttpOnly cookies for session management
- CSRF protection maintained across authentication methods
- Role-based access control preserved

## User Experience

### Login Flow
1. Users visit the login page
2. Available SSO providers appear as buttons below the traditional login form
3. Clicking an SSO provider redirects to the identity provider
4. After successful authentication, users return to DeciFrame
5. New users are automatically provisioned with default permissions

### User Management
- Admins can view OAuth provider information in user management
- Users can be promoted/demoted regardless of authentication method
- Profile information updates from identity provider on each login

## Technical Implementation

### Database Schema
The User model has been extended with OAuth-specific fields:
- `username`: Unique username generated from email
- `oauth_provider`: Identity provider name (google, azure, okta, auth0)
- `oauth_sub`: Provider's unique user identifier
- `first_name`, `last_name`: Name components from provider
- `profile_image_url`: User's profile photo from provider
- `last_login`: Timestamp of last successful authentication

### API Endpoints
- `GET /auth/sso/<provider>`: Initiate SSO login
- `GET /auth/oauth/callback/<provider>`: Handle OAuth callback
- `GET /auth/sso/providers`: Get configured providers (JSON API)

### Error Handling
- Graceful fallback when identity providers are unavailable
- Clear error messages for configuration issues
- Automatic retry mechanisms for temporary failures

## Deployment Considerations

### Environment Variables
Set the required environment variables for your chosen providers in your deployment environment (Replit Secrets, Docker environment, etc.).

### HTTPS Requirements
Most identity providers require HTTPS for production deployments. Ensure your domain has valid SSL certificates.

### Domain Configuration
Update redirect URIs in your identity provider configuration when deploying to production domains.

## Troubleshooting

### Common Issues
1. **Provider not appearing on login page**
   - Check environment variables are properly set
   - Verify provider configuration in identity provider console

2. **Callback errors**
   - Ensure redirect URIs match exactly in provider configuration
   - Check for typos in client ID/secret

3. **User creation failures**
   - Verify email scope is included in provider configuration
   - Check database connectivity and User model compatibility

### Debug Mode
Enable debug logging to see detailed OAuth flow information:
```python
import logging
logging.getLogger('auth.oauth').setLevel(logging.DEBUG)
```

## Security Best Practices
- Regularly rotate client secrets
- Use environment-specific redirect URIs
- Monitor authentication logs for suspicious activity
- Implement proper session timeout policies
- Keep Authlib dependency updated for security patches

## Next Steps
1. Configure your chosen identity providers
2. Set environment variables in your deployment
3. Test authentication flow in development
4. Update redirect URIs for production deployment
5. Train users on new authentication options