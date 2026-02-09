/**
 * Shared Gallery screen - displays circle members' artwork in 2-column grid
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Dimensions,
  TouchableOpacity,
  Alert,
  RefreshControl,
  SafeAreaView,
} from 'react-native';
import { FlashList } from '@shopify/flash-list';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RouteProp } from '@react-navigation/native';
import { CirclesStackParamList } from '../../navigation/types';
import { useCircleGallery, CircleArtwork } from '../../hooks/useCircleGallery';
import { useAuthStore } from '../../store/authStore';
import { getCircleDetail } from '../../services/circles';
import ArtworkCard from '../../components/Circles/ArtworkCard';
import { Circle } from '../../types/circles';

type Props = {
  navigation: NativeStackNavigationProp<CirclesStackParamList, 'SharedGallery'>;
  route: RouteProp<CirclesStackParamList, 'SharedGallery'>;
};

const SCREEN_WIDTH = Dimensions.get('window').width;
const PADDING = 4;
const COLUMN_WIDTH = (SCREEN_WIDTH - PADDING * 3) / 2;

export default function SharedGalleryScreen({ navigation, route }: Props) {
  const { circleId } = route.params;
  const { artworks, loading, error, hasMore, loadMore, refresh } =
    useCircleGallery(circleId);
  const user = useAuthStore((state) => state.user);
  const [circle, setCircle] = useState<Circle | null>(null);
  const [selectedArtworks, setSelectedArtworks] = useState<Set<string>>(
    new Set()
  );
  const [selectionMode, setSelectionMode] = useState(false);

  useEffect(() => {
    loadCircle();
  }, [circleId]);

  const loadCircle = async () => {
    try {
      const circleData = await getCircleDetail(circleId);
      setCircle(circleData);
    } catch (err) {
      console.error('Failed to load circle:', err);
    }
  };

  const handleArtworkPress = (artwork: CircleArtwork) => {
    if (selectionMode) {
      toggleSelection(artwork.artwork_id);
    } else {
      // Regular tap - could navigate to artwork detail in future
      // For now, just show toast
      Alert.alert('Artwork', 'Artwork detail view coming soon');
    }
  };

  const handleArtworkLongPress = (artwork: CircleArtwork) => {
    // Enter selection mode and select this artwork
    if (!selectionMode) {
      setSelectionMode(true);
    }
    toggleSelection(artwork.artwork_id);
  };

  const toggleSelection = (artworkId: string) => {
    setSelectedArtworks((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(artworkId)) {
        newSet.delete(artworkId);
      } else {
        newSet.add(artworkId);
      }
      // Exit selection mode if no items selected
      if (newSet.size === 0) {
        setSelectionMode(false);
      }
      return newSet;
    });
  };

  const handleCreateFusion = () => {
    if (selectedCount < 2 || selectedCount > 4) {
      Alert.alert('Invalid Selection', 'Please select 2-4 artworks to create a fusion.');
      return;
    }
    const artworkIds = Array.from(selectedArtworks);
    navigation.navigate('FusionBuilder', { artworkIds, circleId });
  };

  const handleCreateComposition = () => {
    if (selectedCount < 2 || selectedCount > 4) {
      Alert.alert('Invalid Selection', 'Please select 2-4 artworks for a composition.');
      return;
    }
    const artworkIds = Array.from(selectedArtworks);
    navigation.navigate('CompositionBuilder', { artworkIds, circleId });
  };

  const handleCancelSelection = () => {
    setSelectedArtworks(new Set());
    setSelectionMode(false);
  };

  const renderItem = useCallback(
    ({ item }: { item: CircleArtwork }) => {
      const isSelected = selectedArtworks.has(item.artwork_id);
      const isOwnArtwork = user?.id === item.owner_user_id;

      return (
        <ArtworkCard
          artwork={item}
          isSelected={isSelected}
          onPress={handleArtworkPress}
          onLongPress={handleArtworkLongPress}
          showOwner={true}
          width={COLUMN_WIDTH}
          isOwnArtwork={isOwnArtwork}
        />
      );
    },
    [selectedArtworks, user, selectionMode]
  );

  const renderEmpty = () => {
    if (loading) return null;
    return (
      <View style={styles.emptyContainer}>
        <Text style={styles.emptyText}>No artwork shared yet.</Text>
        <Text style={styles.emptySubtext}>
          Members' processed iris art appears here.
        </Text>
      </View>
    );
  };

  const renderHeader = () => (
    <View style={styles.headerContainer}>
      <Text style={styles.headerTitle}>{circle?.name || 'Shared Gallery'}</Text>
      <Text style={styles.headerSubtitle}>
        {circle?.member_count || 0} {circle?.member_count === 1 ? 'member' : 'members'}
      </Text>
    </View>
  );

  const selectedCount = selectedArtworks.size;

  return (
    <SafeAreaView style={styles.container}>
      <FlashList
        data={artworks}
        renderItem={renderItem}
        keyExtractor={(item) => item.artwork_id}
        numColumns={2}
        estimatedItemSize={COLUMN_WIDTH}
        contentContainerStyle={styles.listContainer}
        ListHeaderComponent={renderHeader}
        ListEmptyComponent={renderEmpty}
        onEndReached={() => {
          if (hasMore && !loading) {
            loadMore();
          }
        }}
        onEndReachedThreshold={0.5}
        refreshControl={
          <RefreshControl
            refreshing={loading}
            onRefresh={refresh}
            tintColor="#007AFF"
          />
        }
      />

      {/* Floating action buttons when 2+ artworks selected */}
      {selectionMode && selectedCount >= 2 && (
        <View style={styles.floatingActionsContainer}>
          <View style={styles.floatingActions}>
            <TouchableOpacity
              style={styles.cancelButton}
              onPress={handleCancelSelection}>
              <Text style={styles.cancelButtonText}>Cancel</Text>
            </TouchableOpacity>

            <View style={styles.actionButtonsRow}>
              <TouchableOpacity
                style={styles.actionButton}
                onPress={handleCreateFusion}>
                <Text style={styles.actionButtonText}>Create Fusion</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.actionButton, styles.actionButtonSecondary]}
                onPress={handleCreateComposition}>
                <Text style={styles.actionButtonText}>Side by Side</Text>
              </TouchableOpacity>
            </View>

            <Text style={styles.selectionCount}>
              {selectedCount} artworks selected
            </Text>
          </View>
        </View>
      )}

      {/* Error toast */}
      {error && (
        <View style={styles.errorContainer}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  listContainer: {
    paddingHorizontal: PADDING,
    paddingTop: 8,
  },
  headerContainer: {
    paddingHorizontal: 12,
    paddingVertical: 16,
    marginBottom: 8,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: '#fff',
    marginBottom: 4,
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#999',
  },
  emptyContainer: {
    paddingVertical: 60,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#666',
    marginBottom: 8,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#999',
    textAlign: 'center',
  },
  floatingActionsContainer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.9)',
    borderTopWidth: 1,
    borderTopColor: '#333',
  },
  floatingActions: {
    padding: 16,
  },
  cancelButton: {
    alignSelf: 'flex-end',
    marginBottom: 12,
  },
  cancelButtonText: {
    color: '#007AFF',
    fontSize: 16,
  },
  actionButtonsRow: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 8,
  },
  actionButton: {
    flex: 1,
    backgroundColor: '#007AFF',
    paddingVertical: 14,
    paddingHorizontal: 20,
    borderRadius: 8,
    alignItems: 'center',
  },
  actionButtonSecondary: {
    backgroundColor: '#5856D6',
  },
  actionButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  selectionCount: {
    textAlign: 'center',
    color: '#999',
    fontSize: 14,
    marginTop: 8,
  },
  errorContainer: {
    position: 'absolute',
    top: 100,
    left: 20,
    right: 20,
    backgroundColor: '#3a0a0a',
    padding: 16,
    borderRadius: 8,
  },
  errorText: {
    color: '#ff453a',
    fontSize: 14,
    textAlign: 'center',
  },
});
