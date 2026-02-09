/**
 * StyleGrid component - displays style presets in a grid layout
 */

import React from 'react';
import {StyleSheet, Text, View, SectionList} from 'react-native';
import {StyleThumbnail} from './StyleThumbnail';
import type {StylePreset} from '../../types/styles';

interface StyleGridProps {
  freeStyles: StylePreset[];
  premiumStyles: StylePreset[];
  onSelect: (preset: StylePreset) => void;
  onPremiumTap: (preset: StylePreset) => void;
  isLoading?: boolean;
}

interface Section {
  title: string;
  data: StylePreset[][];
  tier: string;
}

export function StyleGrid({
  freeStyles,
  premiumStyles,
  onSelect,
  onPremiumTap,
  isLoading,
}: StyleGridProps) {
  // Group styles into rows of 3 for FlatList rendering
  const groupIntoRows = (styles: StylePreset[]): StylePreset[][] => {
    const rows: StylePreset[][] = [];
    for (let i = 0; i < styles.length; i += 3) {
      rows.push(styles.slice(i, i + 3));
    }
    return rows;
  };

  const sections: Section[] = [
    {
      title: 'Free Styles',
      data: groupIntoRows(freeStyles),
      tier: 'free',
    },
    {
      title: 'Premium Styles',
      data: groupIntoRows(premiumStyles),
      tier: 'premium',
    },
  ].filter(section => section.data.length > 0);

  if (isLoading) {
    return (
      <View style={styles.container}>
        <View style={styles.loadingContainer}>
          <Text style={styles.loadingText}>Loading styles...</Text>
        </View>
      </View>
    );
  }

  if (sections.length === 0) {
    return (
      <View style={styles.container}>
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyText}>No styles available</Text>
        </View>
      </View>
    );
  }

  return (
    <SectionList
      sections={sections}
      keyExtractor={(item, index) => `row-${index}`}
      renderItem={({item: row}) => (
        <View style={styles.row}>
          {row.map(preset => (
            <StyleThumbnail
              key={preset.id}
              preset={preset}
              onSelect={onSelect}
              onPremiumTap={onPremiumTap}
            />
          ))}
        </View>
      )}
      renderSectionHeader={({section}) => (
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>{section.title}</Text>
          {section.tier === 'premium' && (
            <Text style={styles.lockIcon}>🔒</Text>
          )}
        </View>
      )}
      contentContainerStyle={styles.listContent}
      stickySectionHeadersEnabled={false}
    />
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#121212',
  },
  listContent: {
    padding: 16,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    gap: 8,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  lockIcon: {
    fontSize: 18,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 16,
    color: '#AAAAAA',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  emptyText: {
    fontSize: 16,
    color: '#AAAAAA',
    textAlign: 'center',
  },
});
