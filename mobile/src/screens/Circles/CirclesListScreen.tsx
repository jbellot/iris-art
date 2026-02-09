/**
 * Circle list screen - browse user's circles
 */
import React, { useEffect } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { CirclesStackParamList } from '../../navigation/types';
import { useCircleStore } from '../../store/circleStore';
import { Circle } from '../../types/circles';

type Props = {
  navigation: NativeStackNavigationProp<CirclesStackParamList, 'CirclesList'>;
};

export default function CirclesListScreen({ navigation }: Props) {
  const { circles, loading, fetchCircles } = useCircleStore();

  useEffect(() => {
    fetchCircles();
  }, []);

  const handleRefresh = async () => {
    await fetchCircles();
  };

  const handleCirclePress = (circle: Circle) => {
    navigation.navigate('CircleDetail', { circleId: circle.id });
  };

  const handleCreatePress = () => {
    navigation.navigate('CreateCircle');
  };

  const renderCircle = ({ item }: { item: Circle }) => {
    const roleBadgeColor = item.role === 'owner' ? '#4CAF50' : '#2196F3';
    const roleLabel = item.role === 'owner' ? 'Owner' : 'Member';

    return (
      <TouchableOpacity
        style={styles.circleCard}
        onPress={() => handleCirclePress(item)}>
        <View style={styles.circleHeader}>
          <Text style={styles.circleName}>{item.name}</Text>
          <View style={[styles.roleBadge, { backgroundColor: roleBadgeColor }]}>
            <Text style={styles.roleText}>{roleLabel}</Text>
          </View>
        </View>
        <Text style={styles.memberCount}>
          {item.member_count} {item.member_count === 1 ? 'member' : 'members'}
        </Text>
      </TouchableOpacity>
    );
  };

  const renderEmpty = () => (
    <View style={styles.emptyContainer}>
      <Text style={styles.emptyText}>No circles yet.</Text>
      <Text style={styles.emptySubtext}>
        Create one to share iris art with friends and family.
      </Text>
    </View>
  );

  if (loading && circles.length === 0) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <FlatList
        data={circles}
        renderItem={renderCircle}
        keyExtractor={(item) => item.id}
        contentContainerStyle={
          circles.length === 0 ? styles.emptyListContainer : styles.listContainer
        }
        refreshControl={
          <RefreshControl refreshing={loading} onRefresh={handleRefresh} />
        }
        ListEmptyComponent={renderEmpty}
      />
      <TouchableOpacity style={styles.fab} onPress={handleCreatePress}>
        <Text style={styles.fabIcon}>+</Text>
      </TouchableOpacity>
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
  listContainer: {
    padding: 16,
  },
  emptyListContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 16,
  },
  circleCard: {
    backgroundColor: '#1A1A1A',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
  },
  circleHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  circleName: {
    fontSize: 18,
    fontWeight: '600',
    color: '#FFF',
    flex: 1,
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
  memberCount: {
    fontSize: 14,
    color: '#999',
  },
  emptyContainer: {
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#FFF',
    marginBottom: 8,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#999',
    textAlign: 'center',
  },
  fab: {
    position: 'absolute',
    right: 16,
    bottom: 16,
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#007AFF',
    justifyContent: 'center',
    alignItems: 'center',
    elevation: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
  },
  fabIcon: {
    fontSize: 32,
    color: '#FFF',
    fontWeight: '300',
  },
});
