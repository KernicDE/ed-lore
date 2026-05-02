import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import Fuse from 'fuse.js';

interface SearchItem {
  id: string;
  title: string;
  type: 'article' | 'entity' | 'arc' | 'location';
  date?: string;
  desc?: string;
  path: string;
  isArticle: boolean;
}

interface CommandConsoleProps {
  searchIndex: { uuid: string; title: string; date: string; body_preview: string }[];
  entities: Record<string, { id: string; name: string; type: string }>;
  arcs: Record<string, { id: string; name: string }>;
  onArticleNavigate: (uuid: string) => void;
  onClose: () => void;
}

export default function CommandConsole({ searchIndex, entities, arcs, onArticleNavigate, onClose }: CommandConsoleProps) {
  const [query, setQuery] = useState('');
  const [selectedIdx, setSelectedIdx] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const baseUrl = (import.meta.env.BASE_URL || '').replace(/\/$/, '');

  const fuse = useMemo(() => {
    const items: SearchItem[] = [
      ...searchIndex.map((a) => ({
        id: a.uuid,
        title: a.title,
        type: 'article' as const,
        date: a.date,
        desc: a.body_preview?.slice(0, 120) + '...',
        path: `${baseUrl}/?article=${a.uuid}`,
        isArticle: true,
      })),
      ...Object.values(entities).map((e) => ({
        id: e.id,
        title: e.name,
        type: 'entity' as const,
        desc: `Type: ${e.type}`,
        path: `${baseUrl}/entity/${e.id}/`,
        isArticle: false,
      })),
      ...Object.values(arcs).map((a) => ({
        id: a.id,
        title: a.name,
        type: 'arc' as const,
        desc: `${a.id.replace(/-/g, ' ')}`,
        path: `${baseUrl}/arc/${a.id}/`,
        isArticle: false,
      })),
    ];
    return new Fuse(items, {
      keys: ['title', 'desc'],
      threshold: 0.3,
      includeScore: true,
    });
  }, [searchIndex, entities, arcs, baseUrl]);

  const results = useMemo(() => {
    if (!query.trim()) return [];
    return fuse.search(query.trim(), { limit: 20 }).map((r) => r.item);
  }, [fuse, query]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  useEffect(() => {
    setSelectedIdx(0);
  }, [query]);

  const handleSelect = useCallback((item: SearchItem) => {
    if (item.isArticle) {
      onArticleNavigate(item.id);
    } else {
      window.location.href = item.path;
    }
  }, [onArticleNavigate]);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
        return;
      }
      if (results.length === 0) return;

      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIdx((i) => (i + 1) % results.length);
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIdx((i) => (i - 1 + results.length) % results.length);
      } else if (e.key === 'Enter') {
        e.preventDefault();
        const item = results[selectedIdx];
        if (item) handleSelect(item);
      }
    },
    [results, selectedIdx, onClose, handleSelect]
  );

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  const typeColors: Record<string, string> = {
    article: 'var(--elite-blue)',
    entity: 'var(--elite-orange)',
    arc: 'var(--elite-green)',
    location: 'var(--elite-yellow)',
  };

  return (
    <div className="search-overlay" onClick={onClose}>
      <div className="search-modal" onClick={(e) => e.stopPropagation()}>
        <div className="search-input-wrap">
          <span style={{ color: 'var(--elite-blue)', marginRight: 12, fontSize: 18 }}>›</span>
          <input
            ref={inputRef}
            className="search-input"
            placeholder="Search articles, entities, arcs..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <span className="search-shortcut">ESC</span>
        </div>
        <div className="search-results">
          {results.length === 0 && query.trim() && (
            <div style={{ padding: 24, textAlign: 'center', color: 'var(--text-dim)', fontSize: 15 }}>
              No results found
            </div>
          )}
          {results.map((item, i) => (
            <div
              key={`${item.type}-${item.id}`}
              className={`search-result ${i === selectedIdx ? 'selected' : ''}`}
              onMouseEnter={() => setSelectedIdx(i)}
              onClick={() => handleSelect(item)}
            >
              <span
                className="search-result-type"
                style={{ borderColor: typeColors[item.type] || 'var(--border-glow)', color: typeColors[item.type] || 'var(--text-dim)' }}
              >
                {item.type}
              </span>
              <div style={{ minWidth: 0 }}>
                <div className="search-result-title">{item.title}</div>
                {item.desc && <div className="search-result-desc">{item.desc}</div>}
                {item.date && (
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-dim)', marginTop: 2 }}>
                    {item.date}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
