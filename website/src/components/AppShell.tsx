import { useState, useCallback, useMemo } from 'react';
import Timeline from './timeline/Timeline';
import ContextPanel from './context/ContextPanel';

interface Article {
  uuid: string;
  title: string;
  slug: string;
  date: string;
  arc_id: string | null;
  significance: string;
  modern_impact: string;
  body_full: string;
  body_preview: string;
  entities: string[];
  groups: string[];
  locations: string[];
  topics: string[];
  legacy_weight: number;
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

// Estimate visible articles from scroll position (sync with Timeline logic)
const ITEM_HEIGHT = 96;
const BUFFER = 8;

export default function AppShell({ articles, entities, arcs }: AppShellProps) {
  const [currentDate, setCurrentDate] = useState('3301-01-01');
  const [selectedArticle, setSelectedArticle] = useState<Article | null>(null);
  const [scrollTop, setScrollTop] = useState(0);
  const [viewportHeight, setViewportHeight] = useState(800);

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

  // Compute visible articles for context panel
  const visibleArticles = useMemo(() => {
    const startIdx = Math.max(0, Math.floor(scrollTop / ITEM_HEIGHT) - BUFFER);
    const endIdx = Math.min(articles.length, Math.ceil((scrollTop + viewportHeight) / ITEM_HEIGHT) + BUFFER);
    return articles.slice(startIdx, endIdx).map((a) => ({
      arc_id: a.arc_id,
      entities: a.entities,
      groups: a.groups,
      locations: a.locations,
      topics: a.topics,
    }));
  }, [scrollTop, viewportHeight, articles]);

  return (
    <div className="main-layout">
      <Timeline
        articles={articles}
        onCenterDateChange={handleCenterDateChange}
        onArticleSelect={handleArticleSelect}
        selectedArticle={selectedArticle}
        onScrollUpdate={handleScrollUpdate}
      />
      <ContextPanel
        currentDate={currentDate}
        entities={entities}
        arcs={arcs}
        visibleArticles={visibleArticles}
      />
    </div>
  );
}
