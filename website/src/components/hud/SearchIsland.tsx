import { useState, useEffect, useCallback } from 'react';
import CommandConsole from './CommandConsole';

type SearchEntry = { uuid: string; title: string; date: string; body_preview: string };
type EntityMap = Record<string, { id: string; name: string; type: string }>;
type ArcMap = Record<string, { id: string; name: string }>;

interface SearchIslandProps {
  baseUrl: string;
}

export default function SearchIsland({ baseUrl }: SearchIslandProps) {
  const [open, setOpen] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [searchIndex, setSearchIndex] = useState<SearchEntry[]>([]);
  const [entities, setEntities] = useState<EntityMap>({});
  const [arcs, setArcs] = useState<ArcMap>({});

  const load = useCallback(async () => {
    if (loaded) return;
    try {
      const [searchData, entityData] = await Promise.all([
        fetch(`${baseUrl}/data/search-index.json`).then((r) => r.json()),
        fetch(`${baseUrl}/data/entities-index.json`).then((r) => r.json()),
      ]);
      setSearchIndex(searchData);
      const ents: EntityMap = {};
      const arcsMap: ArcMap = {};
      for (const item of entityData as { id: string; name: string; type: string }[]) {
        if (item.type === 'arc') arcsMap[item.id] = item;
        else ents[item.id] = item;
      }
      setEntities(ents);
      setArcs(arcsMap);
    } catch {
      // silent fail — search just won't populate
    }
    setLoaded(true);
  }, [loaded, baseUrl]);

  const openSearch = useCallback(() => {
    load();
    setOpen(true);
  }, [load]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        openSearch();
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [openSearch]);

  return (
    <>
      <button className="hud-search-btn" onClick={openSearch} title="Search (Cmd+K)">
        <span style={{ marginRight: 6 }}>⌘</span> Search
      </button>
      {open && (
        <CommandConsole
          searchIndex={searchIndex}
          entities={entities}
          arcs={arcs}
          onArticleNavigate={(uuid) => {
            window.location.href = `${baseUrl}/?article=${uuid}`;
          }}
          onClose={() => setOpen(false)}
        />
      )}
    </>
  );
}
