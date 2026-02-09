/**
 * Join circle screen - accept invite via deep link
 */
import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RouteProp } from '@react-navigation/native';
import { CirclesStackParamList } from '../../navigation/types';
import { getInviteInfo, acceptInvite } from '../../services/invites';
import { useCircleStore } from '../../store/circleStore';
import { InviteInfo } from '../../types/circles';

type Props = {
  navigation: NativeStackNavigationProp<CirclesStackParamList, 'JoinCircle'>;
  route: RouteProp<CirclesStackParamList, 'JoinCircle'>;
};

export default function JoinCircleScreen({ navigation, route }: Props) {
  const { token } = route.params;
  const [inviteInfo, setInviteInfo] = useState<InviteInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [joining, setJoining] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { fetchCircles } = useCircleStore();

  useEffect(() => {
    loadInviteInfo();
  }, []);

  const loadInviteInfo = async () => {
    setLoading(true);
    setError(null);
    try {
      const info = await getInviteInfo(token);
      setInviteInfo(info);
    } catch (err: any) {
      const errorMessage =
        err?.response?.status === 404
          ? 'This invite link is invalid or has expired.'
          : err?.response?.status === 409
          ? 'You are already a member of this circle.'
          : 'Failed to load invite information.';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleJoin = async () => {
    setJoining(true);
    try {
      const { circle_id } = await acceptInvite(token);
      await fetchCircles();
      Alert.alert('Success', 'You have joined the circle!', [
        {
          text: 'OK',
          onPress: () => {
            navigation.navigate('CircleDetail', { circleId: circle_id });
          },
        },
      ]);
    } catch (err: any) {
      const errorMessage =
        err?.response?.status === 404
          ? 'This invite link is invalid or has expired.'
          : err?.response?.status === 409
          ? 'You are already a member of this circle.'
          : err?.response?.status === 400 &&
            err?.response?.data?.detail?.includes('full')
          ? 'This circle is full (maximum 10 members).'
          : 'Failed to join circle. Please try again.';
      Alert.alert('Error', errorMessage);
    } finally {
      setJoining(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Loading invite...</Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.errorContainer}>
        <Text style={styles.errorText}>{error}</Text>
        <TouchableOpacity
          style={styles.button}
          onPress={() => navigation.navigate('CirclesList')}>
          <Text style={styles.buttonText}>Go to My Circles</Text>
        </TouchableOpacity>
      </View>
    );
  }

  if (!inviteInfo) {
    return null;
  }

  return (
    <View style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.title}>You're Invited!</Text>

        <View style={styles.infoCard}>
          <Text style={styles.label}>Circle Name</Text>
          <Text style={styles.value}>{inviteInfo.circle_name}</Text>

          <Text style={styles.label}>Invited by</Text>
          <Text style={styles.value}>{inviteInfo.inviter_email}</Text>

          <Text style={styles.expiryText}>
            Invite expires in {inviteInfo.expires_in_days} days
          </Text>
        </View>

        <TouchableOpacity
          style={[styles.button, joining && styles.buttonDisabled]}
          onPress={handleJoin}
          disabled={joining}>
          {joining ? (
            <ActivityIndicator size="small" color="#FFF" />
          ) : (
            <Text style={styles.buttonText}>Join Circle</Text>
          )}
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.button, styles.buttonSecondary]}
          onPress={() => navigation.navigate('CirclesList')}
          disabled={joining}>
          <Text style={styles.buttonText}>Cancel</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#000',
  },
  loadingText: {
    fontSize: 16,
    color: '#999',
    marginTop: 16,
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#000',
    padding: 16,
  },
  errorText: {
    fontSize: 16,
    color: '#DC3545',
    textAlign: 'center',
    marginBottom: 24,
  },
  content: {
    flex: 1,
    padding: 16,
    justifyContent: 'center',
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: '#FFF',
    textAlign: 'center',
    marginBottom: 32,
  },
  infoCard: {
    backgroundColor: '#1A1A1A',
    borderRadius: 12,
    padding: 20,
    marginBottom: 32,
  },
  label: {
    fontSize: 12,
    color: '#999',
    textTransform: 'uppercase',
    marginTop: 12,
    marginBottom: 4,
  },
  value: {
    fontSize: 18,
    color: '#FFF',
    fontWeight: '600',
  },
  expiryText: {
    fontSize: 12,
    color: '#999',
    marginTop: 16,
    fontStyle: 'italic',
  },
  button: {
    backgroundColor: '#007AFF',
    borderRadius: 8,
    padding: 16,
    alignItems: 'center',
    marginBottom: 12,
  },
  buttonDisabled: {
    opacity: 0.5,
  },
  buttonSecondary: {
    backgroundColor: '#555',
  },
  buttonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFF',
  },
});
