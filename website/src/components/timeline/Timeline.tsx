import { useState, useRef, useCallback, useEffect, useMemo } from 'react';

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

interface TimelineProps {
  articles: Article[];
  onCenterDateChange: (date: string) => void;
  onArticleSelect: (article: Article | null) => void;
  selectedArticle: Article | null;
  onScrollUpdate?: (scrollTop: number, viewportHeight: number) => void;
}

const ITEM_HEIGHT = 96;
const BUFFER = 8;

export default function Timeline({
  articles,
  onCenterDateChange,
  onArticleSelect,
  selectedArticle,
  onScrollUpdate,
}: TimelineProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [scrollTop, setScrollTop] = useState(0);
  const [viewportHeight, setViewportHeight] = useState(800);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const update = () => {
      const vh = el.clientHeight;
      const st = el.scrollTop;
      setViewportHeight(vh);
      setScrollTop(st);
      onScrollUpdate?.(st, vh);
    };
    update();
    el.addEventListener('scroll', update, { passive: true });
    const ro = new ResizeObserver(update);
    ro.observe(el);
    return () => {
      el.removeEventListener('scroll', update);
      ro.disconnect();
    };
  }, []);

  // Compute visible range
  const startIdx = Math.max(0, Math.floor(scrollTop / ITEM_HEIGHT) - BUFFER);
  const endIdx = Math.min(
    articles.length,
    Math.ceil((scrollTop + viewportHeight) / ITEM_HEIGHT) + BUFFER
  );

  // Track center date for time-lock
  useEffect(() => {
    const centerIdx = Math.floor((scrollTop + viewportHeight / 2) / ITEM_HEIGHT);
    const art = articles[Math.min(centerIdx, articles.length - 1)];
    if (art) onCenterDateChange(art.date);
  }, [scrollTop, viewportHeight, articles, onCenterDateChange]);

  // Group by year for sticky headers
  const yearGroups = useMemo(() => {
    const groups: { year: string; startIdx: number }[] = [];
    let lastYear = '';
    articles.forEach((art, i) => {
      const year = art.date?.split('-')[0] ?? 'Unknown';
      if (year !== lastYear) {
        groups.push({ year, startIdx: i });
        lastYear = year;
      }
    });
    return groups;
  }, [articles]);

  const handleItemClick = useCallback((art: Article) => {
    onArticleSelect(selectedArticle?.uuid === art.uuid ? null : art);
  }, [onArticleSelect, selectedArticle]);

  const totalHeight = articles.length * ITEM_HEIGHT;

  return (
    <div ref={containerRef} className="timeline-pane">
      {/* Sticky year headers rendered as absolute overlays */}
      {yearGroups.map((g, i) => {
        const nextStart = yearGroups[i + 1]?.startIdx ?? articles.length;
        const groupTop = g.startIdx * ITEM_HEIGHT;
        const groupBottom = nextStart * ITEM_HEIGHT;
        const visible = scrollTop >= groupTop && scrollTop < groupBottom;
        if (!visible) return null;
        return (
          <div
            key={g.year}
            className="timeline-year-header"
            style={{ position: 'sticky', top: 0 }}
          >
            {g.year}
          </div>
        );
      })}

      <div style={{ height: totalHeight, position: 'relative' }}>
        {articles.slice(startIdx, endIdx).map((art, i) => {
          const idx = startIdx + i;
          const isSelected = selectedArticle?.uuid === art.uuid;
          const sigClass =
            art.significance === 'high'
              ? 'high-significance'
              : art.significance === 'medium'
              ? 'medium-significance'
              : '';

          return (
            <div
              key={art.uuid}
              className={`timeline-item ${sigClass} ${isSelected ? 'active' : ''}`}
              style={{
                position: 'absolute',
                top: idx * ITEM_HEIGHT,
                left: 0,
                right: 0,
                height: isSelected ? 'auto' : ITEM_HEIGHT,
                minHeight: ITEM_HEIGHT,
              }}
              onClick={() => handleItemClick(art)}
            >
              <div className="timeline-date">{art.date}</div>
              <div className="timeline-title">{art.title}</div>
              {!isSelected && (
                <div className="timeline-preview">{art.body_preview}</div>
              )}
              <div className="timeline-meta">
                {art.arc_id && (
                  <span className="timeline-badge arc">{art.arc_id.replace(/-/g, ' ')}</span>
                )}
                {art.topics.slice(0, 2).map((t) => (
                  <span key={t} className="timeline-badge topic">{t}</span>
                ))}
              </div>

              {isSelected && (
                <div className="detail-view">
                  <div className="detail-body">{art.body_full}</div>
                  {art.modern_impact && (
                    <div className="detail-impact">
                      <div className="detail-impact-label">Future Impact Analysis</div>
                      <div className="detail-impact-text">{art.modern_impact}</div>
                    </div>
                  )}
                  {art.entities.length > 0 && (
                    <div style={{ marginTop: 12, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                      {art.entities.slice(0, 6).map((e) => (
                        <span
                          key={e}
                          style={{
                            fontFamily: 'var(--font-mono)',
                            fontSize: 10,
                            color: 'var(--elite-blue)',
                            border: '1px solid var(--elite-blue-dim)',
                            padding: '2px 8px',
                          }}
                        >
                          {e}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
