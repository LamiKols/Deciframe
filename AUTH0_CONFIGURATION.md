# Auth0 Configuration for DeciFrame OIDC Integration

## Auth0 Application Settings

### Application URIs
**Application Login URI:**
```
https://your-replit-app.replit.app/auth/oidc/login
```

**Allowed Callback URLs:**
```
https://your-replit-app.replit.app/auth/oidc/callback
```

**Allowed Logout URLs:**
```
https://your-replit-app.replit.app/
https://your-replit-app.replit.app/auth/login
```

**Allowed Web Origins:**
```
https://your-replit-app.replit.app
```

### Advanced Settings

**Back-Channel Logout URI:**
```
https://your-replit-app.replit.app/auth/oidc/logout/backchannel
```

**Back-Channel Logout Initiators:**
```
https://your-domain.auth0.com
```

## Required Environment Variables

Set these in Replit Secrets:

**OIDC_CLIENT_ID:** `your-auth0-client-id`
**OIDC_CLIENT_SECRET:** `your-auth0-client-secret`
**OIDC_DISCOVERY_URL:** `https://your-domain.auth0.com/.well-known/openid-configuration`
**OIDC_REDIRECT_URI:** `https://your-replit-app.replit.app/auth/oidc/callback`
**OIDC_LOGOUT_URL:** `https://your-domain.auth0.com/v2/logout` (optional)

## Auth0 Application Configuration Steps

### 1. Create Application
- Go to Auth0 Dashboard > Applications
- Click "Create Application"
- Choose "Regular Web Application"
- Select "Python" as technology

### 2. Application Settings
- **Application Type:** Regular Web Application
- **Token Endpoint Authentication Method:** POST
- **Allowed Grant Types:** 
  - Authorization Code
  - Refresh Token
  - Client Credentials

### 3. Connections
Enable the following connections:
- Username-Password-Authentication
- Google (if needed)
- Microsoft (if needed)
- Any other social providers

### 4. Advanced Settings

#### OAuth Tab:
- **JsonWebToken Signature Algorithm:** RS256
- **OIDC Conformant:** Enabled

#### Endpoints Tab:
- **OAuth Authorization URL:** `https://your-domain.auth0.com/authorize`
- **OAuth Token URL:** `https://your-domain.auth0.com/oauth/token`
- **OAuth User Info URL:** `https://your-domain.auth0.com/userinfo`

### 5. APIs & Scopes
Ensure these scopes are available:
- `openid`
- `profile` 
- `email`
- `offline_access` (for refresh tokens)

## User Claims Mapping

Auth0 will provide these claims in the ID token:
```json
{
  "sub": "auth0|user-id",
  "email": "user@example.com",
  "email_verified": true,
  "name": "User Name",
  "given_name": "User",
  "family_name": "Name",
  "picture": "https://...",
  "nickname": "username",
  "updated_at": "2025-06-26T19:00:00.000Z",
  "iss": "https://your-domain.auth0.com/",
  "aud": "your-client-id",
  "iat": 1719423600,
  "exp": 1719460200
}
```

## Rules/Actions (Optional)

Create Auth0 Rules or Actions to:
- Add custom claims (department, role)
- Enforce domain restrictions
- Log authentication events

Example Action to add department:
```javascript
exports.onExecutePostLogin = async (event, api) => {
  const namespace = 'https://deciframe.app/';
  
  // Add custom claims
  api.idToken.setCustomClaim(`${namespace}department`, 'Engineering');
  api.idToken.setCustomClaim(`${namespace}role`, 'Staff');
};
```

## Security Considerations

1. **Domain Validation:** Restrict to your organization's email domains
2. **Rate Limiting:** Configure appropriate rate limits
3. **MFA:** Enable multi-factor authentication
4. **Session Management:** Configure appropriate session timeouts
5. **Audit Logging:** Enable comprehensive audit logs

## Testing the Integration

1. Set all environment variables in Replit Secrets
2. Restart your application
3. Navigate to login page
4. Click "Sign in with SSO" button
5. Verify redirect to Auth0 and successful authentication

## Replace These Placeholders

- `your-replit-app` → Your actual Replit app name
- `your-domain` → Your Auth0 domain (e.g., company.auth0.com)
- `your-auth0-client-id` → Actual client ID from Auth0
- `your-auth0-client-secret` → Actual client secret from Auth0