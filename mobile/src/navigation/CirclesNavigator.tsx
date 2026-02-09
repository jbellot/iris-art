/**
 * Circles stack navigator
 */
import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { CirclesStackParamList } from './types';

// Circle screens
import CirclesListScreen from '../screens/Circles/CirclesListScreen';
import CreateCircleScreen from '../screens/Circles/CreateCircleScreen';
import CircleDetailScreen from '../screens/Circles/CircleDetailScreen';
import InviteScreen from '../screens/Circles/InviteScreen';
import JoinCircleScreen from '../screens/Circles/JoinCircleScreen';

// Placeholder screens (will be implemented in later plans)
import { View, Text, StyleSheet } from 'react-native';

const PlaceholderScreen = ({ title }: { title: string }) => (
  <View style={styles.placeholder}>
    <Text style={styles.placeholderText}>{title}</Text>
    <Text style={styles.placeholderSubtext}>Coming soon</Text>
  </View>
);

const CirclesStack = createNativeStackNavigator<CirclesStackParamList>();

export default function CirclesNavigator() {
  return (
    <CirclesStack.Navigator
      screenOptions={{
        headerStyle: { backgroundColor: '#000' },
        headerTintColor: '#fff',
      }}>
      <CirclesStack.Screen
        name="CirclesList"
        component={CirclesListScreen}
        options={{ title: 'My Circles' }}
      />
      <CirclesStack.Screen
        name="CreateCircle"
        component={CreateCircleScreen}
        options={{ title: 'Create Circle' }}
      />
      <CirclesStack.Screen
        name="CircleDetail"
        component={CircleDetailScreen}
        options={{ title: 'Circle Details' }}
      />
      <CirclesStack.Screen
        name="Invite"
        component={InviteScreen}
        options={{ title: 'Invite Members' }}
      />
      <CirclesStack.Screen
        name="JoinCircle"
        component={JoinCircleScreen}
        options={{ title: 'Join Circle' }}
      />

      {/* Placeholder screens for future plans */}
      <CirclesStack.Screen
        name="SharedGallery"
        options={{ title: 'Shared Gallery' }}>
        {() => <PlaceholderScreen title="Shared Gallery" />}
      </CirclesStack.Screen>
      <CirclesStack.Screen
        name="FusionBuilder"
        options={{ title: 'Create Fusion' }}>
        {() => <PlaceholderScreen title="Fusion Builder" />}
      </CirclesStack.Screen>
      <CirclesStack.Screen
        name="CompositionBuilder"
        options={{ title: 'Compose Fusion' }}>
        {() => <PlaceholderScreen title="Composition Builder" />}
      </CirclesStack.Screen>
      <CirclesStack.Screen
        name="FusionResult"
        options={{ title: 'Fusion Result' }}>
        {() => <PlaceholderScreen title="Fusion Result" />}
      </CirclesStack.Screen>
    </CirclesStack.Navigator>
  );
}

const styles = StyleSheet.create({
  placeholder: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#000',
  },
  placeholderText: {
    fontSize: 24,
    fontWeight: '700',
    color: '#FFF',
    marginBottom: 8,
  },
  placeholderSubtext: {
    fontSize: 16,
    color: '#999',
  },
});
