/**
 * @format
 */

import * as Sentry from '@sentry/react-native';
import { AppRegistry } from 'react-native';
import App from './src/App';
import { name as appName } from './app.json';

Sentry.init({
  dsn: '__SENTRY_DSN__',  // Replace with actual DSN from Sentry project
  environment: __DEV__ ? 'development' : 'production',
  enabled: !__DEV__,
  tracesSampleRate: 0.1,
  beforeSend(event) {
    // Scrub sensitive user data
    if (event.request?.cookies) {
      delete event.request.cookies;
    }
    return event;
  },
});

AppRegistry.registerComponent(appName, () => Sentry.wrap(App));
