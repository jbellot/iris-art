/**
 * Invite screen - generate and share invite link
 */
import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ActivityIndicator,
  Share,
  Clipboard,
} from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RouteProp } from '@react-navigation/native';
import { CirclesStackParamList } from '../../navigation/types';
import { createInvite } from '../../services/invites';
import { InviteResponse } from '../../types/circles';

type Props = {
  navigation: NativeStackNavigationProp<CirclesStackParamList, 'Invite'>;
  route: RouteProp<CirclesStackParamList, 'Invite'>;
};

export default function InviteScreen({ route }: Props) {
  const { circleId } = route.params;
  const [inviteData, setInviteData] = useState<InviteResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    generateInvite();
  }, []);

  const generateInvite = async () => {
    setLoading(true);
    try {
      const data = await createInvite(circleId);
      setInviteData(data);
    } catch (error) {
      Alert.alert('Error', 'Failed to generate invite link');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyLink = () => {
    if (inviteData) {
      Clipboard.setString(inviteData.invite_url);
      Alert.alert('Success', 'Invite link copied to clipboard!');
    }
  };

  const handleShare = async () => {
    if (!inviteData) return;

    try {
      await Share.share({
        message: `Join my IrisVue circle! ${inviteData.invite_url}`,
      });
    } catch (error) {
      // User cancelled or error occurred
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Generating invite link...</Text>
      </View>
    );
  }

  if (!inviteData) {
    return (
      <View style={styles.errorContainer}>
        <Text style={styles.errorText}>Failed to generate invite</Text>
        <TouchableOpacity style={styles.button} onPress={generateInvite}>
          <Text style={styles.buttonText}>Try Again</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.title}>Invite Link</Text>
        <Text style={styles.subtitle}>
          Share this link with people you want to invite to your circle.
        </Text>

        <TextInput
          style={styles.linkInput}
          value={inviteData.invite_url}
          editable={false}
          multiline
        />

        <Text style={styles.expiryText}>
          This link expires in {inviteData.expires_in_days} days
        </Text>

        <TouchableOpacity style={styles.button} onPress={handleCopyLink}>
          <Text style={styles.buttonText}>Copy Link</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.button, styles.buttonSecondary]}
          onPress={handleShare}>
          <Text style={styles.buttonText}>Share</Text>
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
    fontSize: 18,
    color: '#DC3545',
    marginBottom: 24,
  },
  content: {
    flex: 1,
    padding: 16,
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: '#FFF',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 14,
    color: '#999',
    marginBottom: 24,
  },
  linkInput: {
    backgroundColor: '#1A1A1A',
    borderRadius: 8,
    padding: 12,
    fontSize: 14,
    color: '#FFF',
    borderWidth: 1,
    borderColor: '#333',
    minHeight: 80,
    textAlignVertical: 'top',
  },
  expiryText: {
    fontSize: 12,
    color: '#999',
    marginTop: 8,
    marginBottom: 24,
  },
  button: {
    backgroundColor: '#007AFF',
    borderRadius: 8,
    padding: 16,
    alignItems: 'center',
    marginBottom: 12,
  },
  buttonSecondary: {
    backgroundColor: '#4CAF50',
  },
  buttonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFF',
  },
});
