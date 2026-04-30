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
  persons?: string[];
  technologies?: string[];
  player_impact?: string;
  summary?: string;
  related_uuids?: string[];
}

interface TimelineProps {
  articles: Article[];
  onCenterDateChange: (date: string) => void;
  onArticleSelect: (article: Article | null) => void;
  selectedArticle: Article | null;
  onScrollUpdate?: (scrollTop: number, viewportHeight: number) => void;
  scrollToUuid?: string | null;
}

const ITEM_HEIGHT = 100;
const BUFFER = 5;

function wikiLinkToHtml(text: string, baseUrl: string): string {
  return text.replace(/\[\[([^\]]+)\]\]/g, (_match, name) => {
    const eid = name.toLowerCase().replace(/\s+/g, '-').replace(/[^\w-]/g, '');
    return `<a href="${baseUrl}/entity/${eid}/" class="wiki-link">${name}</a>`;
  });
}

function makeEntityId(name: string): string {
  return name.toLowerCase().replace(/\s+/g, '-').replace(/[^\w-]/g, '');
}

function TagList({ items, color, baseUrl }: { items: string[]; color: string; baseUrl: string }) {
  if (!items.length) return null;
  return (
    <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 8 }}>
      {items.map((item) => {
        const eid = makeEntityId(item);
        return (
          <a
            key={item}
            href={`${baseUrl}/entity/${eid}/`}
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 11,
              color,
              border: `1px solid ${color}`,
              padding: '2px 8px',
              opacity: 0.8,
              textDecoration: 'none',
              transition: 'all 0.15s',
            }}
            onMouseEnter={(e) => {
              (e.currentTarget as HTMLElement).style.opacity = '1';
              (e.currentTarget as HTMLElement).style.background = color.replace(')', ', 0.15)').replace('rgb', 'rgba');
            }}
            onMouseLeave={(e) => {
              (e.currentTarget as HTMLElement).style.opacity = '0.8';
              (e.currentTarget as HTMLElement).style.background = 'transparent';
            }}
          >
            {item}
          </a>
        );
      })}
    </div>
  );
}

export default function Timeline({
  articles,
  onCenterDateChange,
  onArticleSelect,
  selectedArticle,
  onScrollUpdate,
  scrollToUuid,
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

  useEffect(() => {
    if (!scrollToUuid || !containerRef.current) return;
    const idx = articles.findIndex((a) => a.uuid === scrollToUuid);
    if (idx === -1) return;
    const el = containerRef.current;
    const targetScroll = idx * ITEM_HEIGHT;
    el.scrollTo({ top: targetScroll, behavior: 'smooth' });
    const art = articles[idx];
    if (art) onArticleSelect(art);
  }, [scrollToUuid, articles, onArticleSelect]);

  useEffect(() => {
    const centerIdx = Math.floor((scrollTop + viewportHeight / 2) / ITEM_HEIGHT);
    const art = articles[Math.min(Math.max(0, centerIdx), articles.length - 1)];
    if (art) onCenterDateChange(art.date);
  }, [scrollTop, viewportHeight, articles, onCenterDateChange]);

  const startIdx = Math.max(0, Math.floor(scrollTop / ITEM_HEIGHT) - BUFFER);
  const endIdx = Math.min(articles.length, Math.ceil((scrollTop + viewportHeight) / ITEM_HEIGHT) + BUFFER);

  const topSpacerHeight = startIdx * ITEM_HEIGHT;
  const bottomSpacerHeight = (articles.length - endIdx) * ITEM_HEIGHT;

  const handleItemClick = useCallback((art: Article) => {
    onArticleSelect(selectedArticle?.uuid === art.uuid ? null : art);
  }, [onArticleSelect, selectedArticle]);

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
                {!isSelected && art.summary && (
                  <div className="timeline-preview">{art.summary}</div>
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
                    {/* Summary Box */}
                    {art.summary && (
                      <div className="detail-summary">
                        <div className="detail-summary-label">Summary</div>
                        <div className="detail-summary-text">{art.summary}</div>
                      </div>
                    )}

                    {/* Full body */}
                    <div
                      className="detail-body"
                      dangerouslySetInnerHTML={{
                        __html: wikiLinkToHtml(art.body_full, baseUrl),
                      }}
                    />

                    {/* Analysis Box */}
                    {(art.player_impact || art.modern_impact) && (
                      <div className="detail-analysis">
                        <div className="detail-analysis-label">Analysis</div>
                        {art.player_impact && (
                          <div className="detail-analysis-section">
                            <div className="detail-analysis-section-label" style={{ color: 'var(--elite-blue)' }}>
                              Player Impact
                            </div>
                            <div className="detail-analysis-section-text">{art.player_impact}</div>
                          </div>
                        )}
                        {art.modern_impact && (
                          <div className="detail-analysis-section">
                            <div className="detail-analysis-section-label" style={{ color: 'var(--elite-orange)' }}>
                              Future Impact
                            </div>
                            <div className="detail-analysis-section-text">{art.modern_impact}</div>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Tags */}
                    <TagList items={art.persons || []} color="var(--elite-blue)" baseUrl={baseUrl} />
                    <TagList items={art.groups || []} color="var(--elite-orange)" baseUrl={baseUrl} />
                    <TagList items={art.technologies || []} color="var(--elite-green)" baseUrl={baseUrl} />
                    <TagList items={art.entities || []} color="var(--elite-yellow)" baseUrl={baseUrl} />
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
