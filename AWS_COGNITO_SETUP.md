# AWS Cognito Setup Guide

This guide will walk you through setting up AWS Cognito User Pool for the MigrateAI application with Google OAuth integration.

## Prerequisites

- AWS Account with appropriate permissions
- AWS CLI configured (optional, but recommended)
- Google Cloud Console access (for OAuth setup)

## Step 1: Create AWS Cognito User Pool

### 1.1 Navigate to AWS Cognito

1. Sign in to AWS Console
2. Navigate to **Cognito** → **User Pools**
3. Click **"Create user pool"**

### 1.2 Configure User Pool Settings

**Pool name:** `migrate-ai-user-pool`

**How do you want to allow users to sign in?**

- ✅ Email
- ✅ Google (we'll configure this later)

**Cognito-assisted verification and confirmation:**

- ❌ No email verification (as per requirements)

### 1.3 Password Policy

**Password requirements:**

- ✅ Require uppercase letters
- ✅ Require lowercase letters
- ✅ Require numbers
- ✅ Require special characters
- **Minimum length:** 8 characters

**Temporary password expiration:** 7 days

### 1.4 MFA and Verifications

**Multi-factor authentication:** Disabled
**User account recovery:** Disabled

### 1.5 Configure App Integration

**App client name:** `migrate-ai-client`
**Confidential client:** No (public client)
**Generate client secret:** No

**Authentication flows:**

- ✅ ALLOW_USER_PASSWORD_AUTH
- ✅ ALLOW_REFRESH_TOKEN_AUTH
- ✅ ALLOW_USER_SRP_AUTH

### 1.6 App Client Settings

**Callback URLs:**

- `http://localhost:3000/callback`
- `http://localhost:8081/callback`
- `http://localhost:8000/api/v1/auth/google/callback`

**Sign out URLs:**

- `http://localhost:3000`
- `http://localhost:8081`
- `http://localhost:8000`

**Allowed OAuth flows:**

- ✅ Authorization code grant
- ✅ Implicit grant

**Allowed OAuth scopes:**

- ✅ email
- ✅ openid
- ✅ profile

### 1.7 Review and Create

Review all settings and click **"Create user pool"**

## Step 2: Configure Google OAuth

### 2.1 Google Cloud Console Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **APIs & Services** → **Credentials**
3. Click **"Create Credentials"** → **"OAuth 2.0 Client IDs"**
4. Configure the OAuth consent screen if prompted

### 2.2 Create OAuth 2.0 Client ID

**Application type:** Web application
**Name:** MigrateAI Web Client
**Authorized JavaScript origins:**

- `http://localhost:3000`
- `http://localhost:8081`
- `http://localhost:8000`

**Authorized redirect URIs:**

- `http://localhost:8000/api/v1/auth/google/callback`
- `http://localhost:3000/callback`
- `http://localhost:8081/callback`

### 2.3 Note Your Credentials

Save the following credentials:

- **Web Client ID:** `your-web-client-id.apps.googleusercontent.com`
- **Web Client Secret:** `your-web-client-secret`

**Note:** For this implementation, we only need the Web Client ID. Platform-specific clients (Android/iOS) are not required as we're using the Web Client ID for both mobile and backend authentication.

## Step 3: Configure Google as Identity Provider in Cognito

### 3.1 Add Google Identity Provider

1. In your Cognito User Pool, go to **Sign-in experience** → **Federated identity provider sign-in**
2. Click **"Add identity provider"**
3. Select **"Google"**

### 3.2 Configure Google Identity Provider

**Google Client ID:** `your-web-client-id.apps.googleusercontent.com`
**Google Client Secret:** `your-web-client-secret`

**Attribute mapping:**

- **Email:** `email`
- **Name:** `name`
- **Given name:** `given_name`
- **Family name:** `family_name`
- **Picture:** `picture`

### 3.3 Configure App Client Integration

1. Go to **App integration** → **App client and analytics**
2. Select your app client
3. Under **Identity providers**, enable **Google**

## Step 4: Environment Configuration

### 4.1 Backend Environment Variables

Add the following to your `.env` file:

```bash
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-web-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-web-client-secret

# AWS Cognito Configuration
COGNITO_USER_POOL_ID=us-east-1_WwRcEUTPK
COGNITO_CLIENT_ID=6ua29lb1du929vuaqllsk2b5tp
COGNITO_CLIENT_SECRET=your-cognito-client-secret

# Backend URL for OAuth callbacks
BACKEND_URL=http://localhost:8000
```

### 4.2 Mobile App Configuration

Update your mobile app configuration:

**Update `src/config/cognito.ts`:**

```typescript
const cognitoConfig = {
  Auth: {
    Cognito: {
      userPoolId: "us-east-1_WwRcEUTPK",
      userPoolClientId: "6ua29lb1du929vuaqllsk2b5tp",
      region: "us-east-1",
      mandatorySignIn: true,
      authenticationFlowType: "USER_PASSWORD_AUTH",
    },
  },
};
```

**Update `src/services/authService.ts`:**

```typescript
GoogleSignin.configure({
  webClientId: "your-web-client-id.apps.googleusercontent.com",
  offlineAccess: true,
  hostedDomain: "",
  forceCodeForRefreshToken: true,
});
```

**Note:** We use the same Web Client ID for both mobile and backend. No platform-specific configuration files are needed.

## Step 5: Testing the Integration

### 5.1 Test Backend OAuth Endpoints

1. Start your backend server
2. Test the Google OAuth endpoints:
   - `GET /api/v1/auth/google/auth-url` - Get authorization URL
   - `POST /api/v1/auth/google/login` - Login with ID token
   - `POST /api/v1/auth/google/callback` - Handle OAuth callback

### 5.2 Test Mobile App Integration

1. Build and run your mobile app
2. Test Google Sign-In flow
3. Verify user creation and authentication

## Troubleshooting

### Common Issues

1. **"Invalid redirect URI" error:**

   - Ensure redirect URIs in Google Console match exactly
   - Check for trailing slashes and protocol differences

2. **"Client ID mismatch" error:**

   - Verify you're using the same Web Client ID for both mobile and backend
   - Check that the client ID matches in your environment variables

3. **"Google Play Services not available" error:**

   - Ensure Google Play Services is installed and updated
   - Test on a device with Google Play Services

4. **"Token validation failed" error:**
   - Check that Google client ID matches between frontend and backend
   - Verify token expiration and audience

### Debug Steps

1. Check browser console for OAuth errors
2. Monitor backend logs for authentication failures
3. Verify environment variables are correctly set
4. Test with Google's OAuth playground

## Security Considerations

1. **Client Secrets:** Never expose client secrets in client-side code
2. **Token Storage:** Store tokens securely using platform-specific secure storage
3. **Token Validation:** Always validate tokens on the backend
4. **HTTPS:** Use HTTPS in production for all OAuth flows
5. **Scope Limitation:** Request only necessary OAuth scopes

## Production Deployment

1. Update redirect URIs for production domains
2. Configure production Google OAuth credentials
3. Update environment variables for production
4. Enable HTTPS for all OAuth endpoints
5. Configure proper CORS settings for production domains
