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
import SharedGalleryScreen from '../screens/Circles/SharedGalleryScreen';
import FusionBuilderScreen from '../screens/Circles/FusionBuilderScreen';
import CompositionBuilderScreen from '../screens/Circles/CompositionBuilderScreen';
import FusionResultScreen from '../screens/Circles/FusionResultScreen';

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

      {/* Fusion and Composition screens */}
      <CirclesStack.Screen
        name="SharedGallery"
        component={SharedGalleryScreen}
        options={{ title: 'Shared Gallery' }}
      />
      <CirclesStack.Screen
        name="FusionBuilder"
        component={FusionBuilderScreen}
        options={{ title: 'Create Fusion' }}
      />
      <CirclesStack.Screen
        name="CompositionBuilder"
        component={CompositionBuilderScreen}
        options={{ title: 'Create Composition' }}
      />
      <CirclesStack.Screen
        name="FusionResult"
        component={FusionResultScreen}
        options={{ title: 'Fusion Result' }}
      />
    </CirclesStack.Navigator>
  );
}
