# AWS Cognito Setup Guide

This guide will walk you through setting up AWS Cognito User Pool for the MigrateAI application.

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

**Sign out URLs:**

- `http://localhost:3000`
- `http://localhost:8081`

**Allowed OAuth flows:**

- ✅ Authorization code grant
- ✅ Implicit grant

**Allowed OAuth scopes:**

- ✅ email
- ✅ openid
- ✅ profile

### 1.7 Review and Create

Review all settings and click **"Create user pool"**

## Step 2: Configure Google OAuth (Optional)

### 2.1 Google Cloud Console Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **APIs & Services** → **Credentials**
3. Click **"Create Credentials"** → **"OAuth 2.0 Client IDs"**
4. Configure the OAuth consent screen if prompted
5. Create OAuth 2.0 Client ID with:
   - **Application type:** Web application
   - **Authorized redirect URIs:** `https://cognito-idp.us-east-1.amazonaws.com/`

### 2.2 Add Google Provider to Cognito

1. In your AWS Cognito User Pool, go to **Sign-in experience** → **Identity providers**
2. Click **"Add identity provider"** → **"Google"**
3. Enter your Google Client ID and Client Secret
4. Save the configuration

## Step 3: Get Configuration Values

After creating the User Pool, note down these values:

1. **User Pool ID** (format: `us-east-1_xxxxxxxxx`)
2. **App Client ID** (format: `xxxxxxxxxxxxxxxxxxxxxxxxxx`)

## Step 4: Update Environment Configuration

Update your `.env.local` file with the actual values:

```bash
# AWS Cognito Configuration
AWS_REGION=us-east-1
COGNITO_USER_POOL_ID=us-east-1_xxxxxxxxx  # Replace with actual User Pool ID
COGNITO_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxx  # Replace with actual Client ID
COGNITO_CLIENT_SECRET=  # Leave empty for public client

# AWS Credentials (for local development)
AWS_ACCESS_KEY_ID=your-actual-access-key
AWS_SECRET_ACCESS_KEY=your-actual-secret-key
```

## Step 5: Test Configuration

Run the test script to verify your setup:

```bash
python test_cognito_setup.py
```

## Step 6: Custom Attributes (Optional)

If you want to store additional user attributes, you can add custom attributes:

1. In your User Pool, go to **Sign-up experience** → **Custom attributes**
2. Add custom attributes for:
   - `age` (Number)
   - `marital_status` (String)
   - `profession` (String)
   - `dependents` (Number)

## Troubleshooting

### Common Issues

1. **"Parameter validation failed"**

   - Check that all environment variables are set correctly
   - Ensure AWS credentials have proper permissions

2. **"Access Denied"**

   - Verify AWS credentials have Cognito permissions
   - Check IAM policies for Cognito access

3. **"Invalid client"**
   - Verify App Client ID is correct
   - Check that the client is configured for the correct auth flows

### Required IAM Permissions

Your AWS user/role needs these Cognito permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cognito-idp:CreateUserPool",
        "cognito-idp:CreateUserPoolClient",
        "cognito-idp:DescribeUserPool",
        "cognito-idp:DescribeUserPoolClient",
        "cognito-idp:AdminCreateUser",
        "cognito-idp:AdminGetUser",
        "cognito-idp:AdminUpdateUserAttributes",
        "cognito-idp:AdminDeleteUser",
        "cognito-idp:InitiateAuth",
        "cognito-idp:RespondToAuthChallenge",
        "cognito-idp:ForgotPassword",
        "cognito-idp:ConfirmForgotPassword",
        "cognito-idp:GetUser"
      ],
      "Resource": "*"
    }
  ]
}
```

## Next Steps

After completing this setup:

1. Test user registration and login
2. Update authentication endpoints to use Cognito
3. Configure mobile app to use Cognito SDK
4. Set up production environment variables
