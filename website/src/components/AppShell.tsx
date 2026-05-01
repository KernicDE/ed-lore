import { useState, useCallback, useMemo, useEffect } from 'react';
import Timeline from './timeline/Timeline';
import ContextPanel from './context/ContextPanel';
import CommandConsole from './hud/CommandConsole';

interface Article {
  uuid: string;
  title: string;
  slug: string;
  date: string;
  arc_id: string | null;
  significance: string;
  summary: string;
  player_impact: string;
  modern_impact: string;
  body_full: string;
  body_preview: string;
  entities: string[];
  groups: string[];
  locations: string[];
  topics: string[];
  legacy_weight: number;
  persons?: string[];
  technologies?: string[];
}

interface Entity {
  id: string;
  name: string;
  type: string;
  first_seen_date: string;
  last_seen_date: string;
  mention_count: number;
}

interface Arc {
  id: string;
  name: string;
  first_seen_date: string;
  last_seen_date: string;
  mention_count: number;
  key_entities: { id: string; mentions: number }[];
}

interface AppShellProps {
  articles: Article[];
  entities: Record<string, Entity>;
  arcs: Record<string, Arc>;
}

export default function AppShell({ articles, entities, arcs }: AppShellProps) {
  const [currentDate, setCurrentDate] = useState('3312-12-31');
  const [selectedArticle, setSelectedArticle] = useState<Article | null>(null);
  const [scrollTop, setScrollTop] = useState(0);
  const [viewportHeight, setViewportHeight] = useState(800);
  const [scrollToUuid, setScrollToUuid] = useState<string | null>(null);
  const [searchOpen, setSearchOpen] = useState(false);

  // Newest first (descending)
  const sortedArticles = useMemo(() => {
    return [...articles].sort((a, b) => (b.date || '').localeCompare(a.date || ''));
  }, [articles]);

  // Extract all unique years from articles, sorted descending
  const allYears = useMemo(() => {
    const yearSet = new Set<string>();
    sortedArticles.forEach((a) => {
      const year = a.date?.split('-')[0];
      if (year) yearSet.add(year);
    });
    return Array.from(yearSet).sort((a, b) => b.localeCompare(a));
  }, [sortedArticles]);

  // Handle ?article=uuid query param on mount (for navigation from entity/arc pages)
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const targetUuid = params.get('article');
    if (targetUuid) {
      setScrollToUuid(targetUuid);
      window.history.replaceState({}, '', window.location.pathname);
    }
  }, []);

  const handleCenterDateChange = useCallback((date: string) => {
    setCurrentDate(date);
  }, []);

  const handleArticleSelect = useCallback((article: Article | null) => {
    setSelectedArticle(article);
  }, []);

  const handleScrollUpdate = useCallback((st: number, vh: number) => {
    setScrollTop(st);
    setViewportHeight(vh);
  }, []);

  const handleArticleNavigate = useCallback((uuid: string) => {
    setScrollToUuid(uuid);
    setSearchOpen(false);
    setTimeout(() => setScrollToUuid(null), 1000);
  }, []);

  const handleYearSelect = useCallback((year: string) => {
    // Find first article of this year (articles are sorted newest first)
    const idx = sortedArticles.findIndex((a) => a.date?.startsWith(year));
    if (idx !== -1) {
      const art = sortedArticles[idx];
      setScrollToUuid(art.uuid);
      setSelectedArticle(null);
      setTimeout(() => setScrollToUuid(null), 1000);
    }
  }, [sortedArticles]);

  // Listen for header search button click
  useEffect(() => {
    const onOpen = () => setSearchOpen(true);
    window.addEventListener('galnet-open-search', onOpen);
    return () => window.removeEventListener('galnet-open-search', onOpen);
  }, []);

  // Keyboard: Cmd+K opens search, ESC closes it
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setSearchOpen(true);
      }
      if (e.key === 'Escape' && searchOpen) {
        e.preventDefault();
        setSearchOpen(false);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [searchOpen]);

  // Build visible articles for context panel (simpler without virtualization)
  const visibleArticles = useMemo(() => {
    return sortedArticles.map((a) => ({
      arc_id: a.arc_id,
      entities: a.entities,
      groups: a.groups,
      locations: a.locations,
      topics: a.topics,
      persons: a.persons || [],
      technologies: a.technologies || [],
    }));
  }, [sortedArticles]);

  return (
    <>
      <div className="main-layout">
        <Timeline
          articles={sortedArticles}
          onCenterDateChange={handleCenterDateChange}
          onArticleSelect={handleArticleSelect}
          selectedArticle={selectedArticle}
          onScrollUpdate={handleScrollUpdate}
          scrollToUuid={scrollToUuid}
        />
        <ContextPanel
          currentDate={currentDate}
          entities={entities}
          arcs={arcs}
          visibleArticles={visibleArticles}
          allYears={allYears}
          onYearSelect={handleYearSelect}
        />
      </div>
      {searchOpen && (
        <CommandConsole
          articles={articles}
          entities={entities}
          arcs={arcs}
          onArticleNavigate={handleArticleNavigate}
          onClose={() => setSearchOpen(false)}
        />
      )}
    </>
  );
}
