import type { Collection } from '@/lib/types';

export type CollectionState = 'loading' | 'ready' | 'empty' | 'error';

export type CollectionMutation =
  | { revision: number; type: 'create'; name: string }
  | { revision: number; type: 'rename'; oldName: string; newName: string }
  | { revision: number; type: 'delete'; name: string };

export interface CollectionSourceProps {
  collections: Collection[];
  collectionState: CollectionState;
  collectionError: string;
  collectionMutation: CollectionMutation | null;
  onRetryCollections: () => void;
}

export function resolveCollectionSelection(
  current: string | undefined,
  collections: Collection[],
  mutation: CollectionMutation | null,
  handledMutationRevision: number,
): string | undefined {
  if (
    mutation?.type === 'rename' &&
    mutation.revision > handledMutationRevision &&
    current === mutation.oldName
  ) {
    return mutation.newName;
  }

  if (current && collections.some((collection) => collection.name === current)) {
    return current;
  }

  return collections[0]?.name;
}
