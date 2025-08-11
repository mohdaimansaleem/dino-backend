# Google Cloud Authentication Setup

## Option 1: Service Account Key (Recommended for Local Development)

1. **Create a service account key:**
   ```bash
   # Go to Google Cloud Console
   # Navigate to IAM & Admin > Service Accounts
   # Create or select a service account
   # Create a new key (JSON format)
   # Download the key file
   ```

2. **Set the environment variable:**
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"
   ```

3. **Add to your shell profile:**
   ```bash
   echo 'export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"' >> ~/.zshrc
   source ~/.zshrc
   ```

## Option 2: gcloud CLI Authentication

1. **Install gcloud CLI:**
   ```bash
   # macOS
   brew install google-cloud-sdk
   
   # Or download from: https://cloud.google.com/sdk/docs/install
   ```

2. **Authenticate:**
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   gcloud auth application-default login
   ```

## Option 3: Use Firestore Emulator (Local Development)

1. **Install Firebase CLI:**
   ```bash
   npm install -g firebase-tools
   ```

2. **Start Firestore emulator:**
   ```bash
   firebase emulators:start --only firestore
   ```

3. **Set environment variable:**
   ```bash
   export FIRESTORE_EMULATOR_HOST="localhost:8080"
   ```

## Verify Authentication

Test your setup:
```bash
gcloud auth list
gcloud config list project
```