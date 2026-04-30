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
const BUFFER = 5;

function wikiLinkToHtml(text: string, baseUrl: string): string {
  return text.replace(/\[\[([^\]]+)\]\]/g, (_match, name) => {
    const eid = name.toLowerCase().replace(/[^\w-]/g, '').replace(/\s+/g, '-');
    return `<a href="${baseUrl}entity/${eid}/" class="wiki-link">${name}</a>`;
  });
}

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

  const baseUrl = (import.meta.env.BASE_URL || '').replace(/\/$/, '');

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
  }, [onScrollUpdate]);

  // Track center date for time-lock
  useEffect(() => {
    const centerIdx = Math.floor((scrollTop + viewportHeight / 2) / ITEM_HEIGHT);
    const art = articles[Math.min(Math.max(0, centerIdx), articles.length - 1)];
    if (art) onCenterDateChange(art.date);
  }, [scrollTop, viewportHeight, articles, onCenterDateChange]);

  // Virtualisation with spacers (normal flow, no absolute positioning)
  const startIdx = Math.max(0, Math.floor(scrollTop / ITEM_HEIGHT) - BUFFER);
  const endIdx = Math.min(articles.length, Math.ceil((scrollTop + viewportHeight) / ITEM_HEIGHT) + BUFFER);

  const topSpacerHeight = startIdx * ITEM_HEIGHT;
  const bottomSpacerHeight = (articles.length - endIdx) * ITEM_HEIGHT;

  const handleItemClick = useCallback((art: Article) => {
    onArticleSelect(selectedArticle?.uuid === art.uuid ? null : art);
  }, [onArticleSelect, selectedArticle]);

  // Group by year for sticky headers among visible items
  const visibleArticles = articles.slice(startIdx, endIdx);
  const yearHeaders = useMemo(() => {
    const headers: { year: string; index: number }[] = [];
    let lastYear = '';
    visibleArticles.forEach((art, i) => {
      const year = art.date?.split('-')[0] ?? 'Unknown';
      if (year !== lastYear) {
        headers.push({ year, index: startIdx + i });
        lastYear = year;
      }
    });
    return headers;
  }, [visibleArticles, startIdx]);

  return (
    <div ref={containerRef} className="timeline-pane">
      <div style={{ paddingTop: topSpacerHeight, paddingBottom: bottomSpacerHeight }}>
        {visibleArticles.map((art, i) => {
          const globalIdx = startIdx + i;
          const isSelected = selectedArticle?.uuid === art.uuid;
          const sigClass =
            art.significance === 'high'
              ? 'high-significance'
              : art.significance === 'medium'
              ? 'medium-significance'
              : '';

          const showYearHeader = yearHeaders.some((h) => h.index === globalIdx);

          return (
            <div key={art.uuid}>
              {showYearHeader && (
                <div className="timeline-year-header">
                  {art.date?.split('-')[0] || 'Unknown'}
                </div>
              )}
              <div
                className={`timeline-item ${sigClass} ${isSelected ? 'active' : ''}`}
                style={{ minHeight: ITEM_HEIGHT }}
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
                    <div
                      className="detail-body"
                      dangerouslySetInnerHTML={{
                        __html: wikiLinkToHtml(art.body_full, baseUrl),
                      }}
                    />
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
            </div>
          );
        })}
      </div>
    </div>
  );
}
