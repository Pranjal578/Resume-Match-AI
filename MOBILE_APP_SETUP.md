# Resume Match AI - React Native Mobile App

A cross-platform mobile application for Resume Match AI, built with React Native and Expo.

## Features

- 📱 iOS & Android support
- 📤 Upload resumes (PDF, DOCX, TXT)
- 🔍 Real-time resume parsing
- 📊 Match resumes against job descriptions
- 📈 View detailed matching analytics
- 💾 Manage resume library
- 🎨 Beautiful, intuitive UI

## Project Structure

```
resume-match-ai-mobile/
├── app/
│   ├── components/          # Reusable UI components
│   ├── screens/             # Main app screens
│   ├── services/            # API integration
│   ├── context/             # React context for state
│   ├── utils/               # Utility functions
│   └── styles/              # Shared styling
├── assets/                  # Images, fonts, etc.
├── app.json                 # Expo configuration
├── App.tsx                  # Main app file
├── package.json             # Dependencies
├── tsconfig.json            # TypeScript config
└── .env.example             # Environment variables template
```

## Prerequisites

- Node.js 16+ 
- npm or yarn
- Expo CLI: `npm install -g expo-cli`
- iOS: Xcode (for iOS development)
- Android: Android Studio (for Android development)

## Setup Instructions

1. **Create the React Native project**:
   ```bash
   npx create-expo-app resume-match-ai-mobile
   cd resume-match-ai-mobile
   ```

2. **Install dependencies**:
   ```bash
   npm install expo
   npm install @react-navigation/native @react-navigation/bottom-tabs @react-navigation/stack
   npm install react-native-screens react-native-safe-area-context react-native-gesture-handler react-native-reanimated
   npm install axios react-native-document-picker react-native-fs
   npm install typescript @types/react @types/react-native
   npm install @react-native-async-storage/async-storage
   ```

3. **Create `.env` file**:
   ```
   EXPO_PUBLIC_API_URL=http://localhost:8000
   ```

4. **Run the app**:
   - Expo Go (easiest for development):
     ```bash
     npx expo start
     ```
   - Or build locally:
     ```bash
     npx expo run:ios      # for iOS
     npx expo run:android  # for Android
     ```

## API Integration

The mobile app connects to the FastAPI backend at the URL specified in `.env.example`.

### Key Endpoints Used:

- `POST /resumes/upload` - Upload a resume
- `GET /resumes/list` - List all resumes
- `DELETE /resumes/{resume_id}` - Delete a resume
- `POST /match/single` - Match single resume
- `POST /match/batch` - Match all resumes
- `GET /health` - Health check
- `GET /info` - Service info

## Development Workflow

1. Start the FastAPI backend:
   ```bash
   cd ../resume-match-ai
   python -m pip install -r requirements.txt
   python -m src.api
   ```

2. Start the React Native development server:
   ```bash
   cd resume-match-ai-mobile
   npx expo start
   ```

3. Scan the QR code with Expo Go app (iOS/Android) or press 'i'/'a' for simulators

## Building for Production

### iOS:
```bash
npx eas build --platform ios
npx eas submit --platform ios
```

### Android:
```bash
npx eas build --platform android
npx eas submit --platform android
```

## Environment Configuration

Create `.env` file in project root:
```
EXPO_PUBLIC_API_URL=https://your-api-domain.com
EXPO_PUBLIC_API_TIMEOUT=30000
```

## Debugging

- Use React Native Debugger
- Enable Flipper for debugging network requests
- Check Expo logs: `expo start --clear`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT
