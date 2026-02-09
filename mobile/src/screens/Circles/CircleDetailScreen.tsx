/**
 * Circle detail screen - view members and manage circle
 */
import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RouteProp } from '@react-navigation/native';
import { CirclesStackParamList } from '../../navigation/types';
import { useCircleStore } from '../../store/circleStore';
import { getCircleDetail, getCircleMembers, leaveCircle, removeMember } from '../../services/circles';
import { Circle, CircleMember } from '../../types/circles';

type Props = {
  navigation: NativeStackNavigationProp<CirclesStackParamList, 'CircleDetail'>;
  route: RouteProp<CirclesStackParamList, 'CircleDetail'>;
};

export default function CircleDetailScreen({ navigation, route }: Props) {
  const { circleId } = route.params;
  const [circle, setCircle] = useState<Circle | null>(null);
  const [members, setMembers] = useState<CircleMember[]>([]);
  const [loading, setLoading] = useState(true);
  const { removeCircle: removeCircleFromStore } = useCircleStore();

  useEffect(() => {
    loadCircleData();
  }, [circleId]);

  const loadCircleData = async () => {
    setLoading(true);
    try {
      const [circleData, membersData] = await Promise.all([
        getCircleDetail(circleId),
        getCircleMembers(circleId),
      ]);
      setCircle(circleData);
      setMembers(membersData);
    } catch (error) {
      Alert.alert('Error', 'Failed to load circle data');
      navigation.goBack();
    } finally {
      setLoading(false);
    }
  };

  const handleInvitePress = () => {
    navigation.navigate('Invite', { circleId });
  };

  const handleSharedGalleryPress = () => {
    Alert.alert('Coming soon', 'Shared gallery feature is coming soon!');
  };

  const handleLeaveCircle = () => {
    if (!circle) return;

    const isLastOwner =
      circle.role === 'owner' && circle.member_count === 1;
    const warningMessage = isLastOwner
      ? 'This will delete the circle as you are the last member.'
      : 'Are you sure you want to leave this circle?';

    Alert.alert('Leave Circle', warningMessage, [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Leave',
        style: 'destructive',
        onPress: async () => {
          try {
            await leaveCircle(circleId);
            removeCircleFromStore(circleId);
            navigation.goBack();
          } catch (error) {
            Alert.alert('Error', 'Failed to leave circle');
          }
        },
      },
    ]);
  };

  const handleRemoveMember = (member: CircleMember) => {
    Alert.alert(
      'Remove Member',
      `Remove ${member.email} from this circle?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Remove',
          style: 'destructive',
          onPress: async () => {
            try {
              await removeMember(circleId, member.user_id);
              setMembers((prev) =>
                prev.filter((m) => m.user_id !== member.user_id)
              );
              if (circle) {
                setCircle({
                  ...circle,
                  member_count: circle.member_count - 1,
                });
              }
            } catch (error) {
              Alert.alert('Error', 'Failed to remove member');
            }
          },
        },
      ]
    );
  };

  const renderMember = ({ item }: { item: CircleMember }) => {
    const isOwner = circle?.role === 'owner';
    const canRemove = isOwner && item.role !== 'owner';

    return (
      <TouchableOpacity
        style={styles.memberCard}
        onLongPress={() => canRemove && handleRemoveMember(item)}
        disabled={!canRemove}>
        <View>
          <Text style={styles.memberEmail}>{item.email}</Text>
          <Text style={styles.memberDate}>
            Joined {new Date(item.joined_at).toLocaleDateString()}
          </Text>
        </View>
        <View
          style={[
            styles.roleBadge,
            { backgroundColor: item.role === 'owner' ? '#4CAF50' : '#2196F3' },
          ]}>
          <Text style={styles.roleText}>
            {item.role === 'owner' ? 'Owner' : 'Member'}
          </Text>
        </View>
      </TouchableOpacity>
    );
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
      </View>
    );
  }

  if (!circle) {
    return null;
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.circleName}>{circle.name}</Text>
        <Text style={styles.memberCount}>
          {circle.member_count} {circle.member_count === 1 ? 'member' : 'members'}
        </Text>
      </View>

      <FlatList
        data={members}
        renderItem={renderMember}
        keyExtractor={(item) => item.user_id}
        contentContainerStyle={styles.listContainer}
        ListHeaderComponent={
          <Text style={styles.sectionTitle}>Members</Text>
        }
      />

      <View style={styles.buttonContainer}>
        <TouchableOpacity
          style={styles.button}
          onPress={handleInvitePress}>
          <Text style={styles.buttonText}>Invite Members</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.button, styles.buttonSecondary]}
          onPress={handleSharedGalleryPress}>
          <Text style={styles.buttonText}>Shared Gallery</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.button, styles.buttonDanger]}
          onPress={handleLeaveCircle}>
          <Text style={styles.buttonText}>Leave Circle</Text>
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
  header: {
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#333',
  },
  circleName: {
    fontSize: 24,
    fontWeight: '700',
    color: '#FFF',
    marginBottom: 4,
  },
  memberCount: {
    fontSize: 14,
    color: '#999',
  },
  listContainer: {
    padding: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#FFF',
    marginBottom: 12,
  },
  memberCard: {
    backgroundColor: '#1A1A1A',
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  memberEmail: {
    fontSize: 16,
    color: '#FFF',
    marginBottom: 2,
  },
  memberDate: {
    fontSize: 12,
    color: '#999',
  },
  roleBadge: {
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
  },
  roleText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#FFF',
  },
  buttonContainer: {
    padding: 16,
    gap: 12,
  },
  button: {
    backgroundColor: '#007AFF',
    borderRadius: 8,
    padding: 16,
    alignItems: 'center',
  },
  buttonSecondary: {
    backgroundColor: '#555',
  },
  buttonDanger: {
    backgroundColor: '#DC3545',
  },
  buttonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFF',
  },
});
