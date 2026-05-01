import { useState, useRef, useCallback, useEffect, useMemo } from 'react';

interface Article {
  uuid: string;
  title: string;
  slug: string;
  date: string;
  arc_id: string | null;
  significance: string;
  modern_impact: string;
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
  bodies: Record<string, string> | null;
  onNeedBodies: () => void;
  onCenterDateChange: (date: string) => void;
  onArticleSelect: (article: Article | null) => void;
  selectedArticle: Article | null;
  onScrollUpdate?: (scrollTop: number, viewportHeight: number) => void;
  onVisibleArticlesChange?: (visibleUuids: string[]) => void;
  scrollToUuid?: string | null;
}

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

function CopyLinkButton({ uuid }: { uuid: string }) {
  const [copied, setCopied] = useState(false);
  const baseUrl = (import.meta.env.BASE_URL || '').replace(/\/$/, '');

  const handleClick = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    const url = `${window.location.origin}${baseUrl}/?article=${uuid}`;
    navigator.clipboard.writeText(url).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }, [uuid, baseUrl]);

  return (
    <button
      onClick={handleClick}
      title="Copy link to article"
      style={{
        background: 'transparent',
        border: '1px solid var(--border-glow)',
        color: copied ? 'var(--elite-green)' : 'var(--text-dim)',
        fontFamily: 'var(--font-mono)',
        fontSize: 11,
        padding: '4px 10px',
        cursor: 'pointer',
        transition: 'all 0.15s',
        flexShrink: 0,
      }}
    >
      {copied ? 'Copied!' : '🔗 Link'}
    </button>
  );
}

function PlayAudioButton({ uuid, title }: { uuid: string; title: string }) {
  const handleClick = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    window.dispatchEvent(new CustomEvent('galnet-audio-play', { detail: { uuid, title } }));
  }, [uuid, title]);

  return (
    <button
      onClick={handleClick}
      title="Play audio"
      style={{
        background: 'transparent',
        border: '1px solid var(--elite-orange-dim)',
        color: 'var(--elite-orange)',
        fontFamily: 'var(--font-mono)',
        fontSize: 11,
        padding: '4px 10px',
        cursor: 'pointer',
        transition: 'all 0.15s',
        flexShrink: 0,
        marginTop: 6,
      }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLElement).style.background = 'var(--elite-orange)';
        (e.currentTarget as HTMLElement).style.color = 'var(--bg-primary)';
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLElement).style.background = 'transparent';
        (e.currentTarget as HTMLElement).style.color = 'var(--elite-orange)';
      }}
    >
      ▶ Audio
    </button>
  );
}

export default function Timeline({
  articles,
  bodies,
  onNeedBodies,
  onCenterDateChange,
  onArticleSelect,
  selectedArticle,
  onScrollUpdate,
  onVisibleArticlesChange,
  scrollToUuid,
}: TimelineProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const itemRefs = useRef<Map<string, HTMLDivElement>>(new Map());
  const yearHeaderRefs = useRef<Map<string, HTMLDivElement>>(new Map());

  const baseUrl = (import.meta.env.BASE_URL || '').replace(/\/$/, '');

  const prevSelectedUuid = useRef<string | null>(null);

  // Extract unique years (oldest → newest for slider)
  const sliderYears = useMemo(() => {
    const set = new Set<string>();
    articles.forEach((a) => {
      const y = a.date?.split('-')[0];
      if (y) set.add(y);
    });
    return Array.from(set).sort((a, b) => a.localeCompare(b));
  }, [articles]);

  const [visibleYear, setVisibleYear] = useState(sliderYears[sliderYears.length - 1] || '');

  // Scroll to article on mount when ?article=uuid is present
  useEffect(() => {
    if (!scrollToUuid) return;
    const el = itemRefs.current.get(scrollToUuid);
    if (el && containerRef.current) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      const art = articles.find((a) => a.uuid === scrollToUuid);
      if (art) onArticleSelect(art);
    }
  }, [scrollToUuid, articles, onArticleSelect]);

  // When a new article is selected, scroll it to the top of the viewport
  useEffect(() => {
    if (!selectedArticle) {
      prevSelectedUuid.current = null;
      return;
    }
    if (prevSelectedUuid.current === selectedArticle.uuid) return;
    prevSelectedUuid.current = selectedArticle.uuid;

    const el = itemRefs.current.get(selectedArticle.uuid);
    const container = containerRef.current;
    if (!el || !container) return;

    requestAnimationFrame(() => {
      const containerRect = container.getBoundingClientRect();
      const elRect = el.getBoundingClientRect();
      const stickyHeaderOffset = 52; // account for sticky year header
      const targetScroll = container.scrollTop + (elRect.top - containerRect.top) - stickyHeaderOffset;
      container.scrollTo({ top: Math.max(0, targetScroll), behavior: 'smooth' });
    });
  }, [selectedArticle]);

  // Report scroll position + track visible year + compute visible articles
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const update = () => {
      onScrollUpdate?.(el.scrollTop, el.clientHeight);

      // Find which year header is currently at/near the top
      let bestYear = '';
      let bestTop = -Infinity;
      yearHeaderRefs.current.forEach((headerEl, year) => {
        const rect = headerEl.getBoundingClientRect();
        const containerRect = el.getBoundingClientRect();
        const top = rect.top - containerRect.top;
        // We want the header that is at or just above the viewport top
        if (top <= 40 && top > bestTop) {
          bestTop = top;
          bestYear = year;
        }
      });
      if (bestYear) setVisibleYear(bestYear);

      // Compute visible articles (within viewport + padding)
      const visibleUuids: string[] = [];
      const containerRect = el.getBoundingClientRect();
      const pad = 200; // Include articles just above/below viewport
      itemRefs.current.forEach((itemEl, uuid) => {
        const rect = itemEl.getBoundingClientRect();
        const top = rect.top - containerRect.top;
        const bottom = rect.bottom - containerRect.top;
        if (bottom >= -pad && top <= el.clientHeight + pad) {
          visibleUuids.push(uuid);
        }
      });
      onVisibleArticlesChange?.(visibleUuids);

      // Also update center date for context panel
      const centerY = el.scrollTop + el.clientHeight / 2;
      let closest: { idx: number; dist: number } = { idx: 0, dist: Infinity };
      itemRefs.current.forEach((itemEl, uuid) => {
        const rect = itemEl.getBoundingClientRect();
        const containerRect = el.getBoundingClientRect();
        const itemCenter = rect.top - containerRect.top + rect.height / 2;
        const dist = Math.abs(itemCenter - el.clientHeight / 2);
        if (dist < closest.dist) {
          closest = { idx: articles.findIndex((a) => a.uuid === uuid), dist };
        }
      });
      const art = articles[closest.idx];
      if (art) onCenterDateChange(art.date);
    };
    el.addEventListener('scroll', update, { passive: true });
    update();
    return () => el.removeEventListener('scroll', update);
  }, [articles, onCenterDateChange, onScrollUpdate, onVisibleArticlesChange]);

  const handleHeaderClick = useCallback((art: Article) => {
    onArticleSelect(selectedArticle?.uuid === art.uuid ? null : art);
  }, [onArticleSelect, selectedArticle]);

  const handleSliderChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const idx = parseInt(e.target.value, 10);
    const year = sliderYears[idx];
    if (!year) return;

    // Find first article of this year and scroll to it
    const firstArt = articles.find((a) => a.date?.startsWith(year));
    if (firstArt && containerRef.current) {
      const el = itemRefs.current.get(firstArt.uuid);
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'start' });
        onArticleSelect(null); // close any open article
      }
    }
  }, [sliderYears, articles, onArticleSelect]);

  // Group articles by year for rendering
  const yearGroups = useMemo(() => {
    const groups: { year: string; articles: Article[] }[] = [];
    let currentYear = '';
    articles.forEach((art) => {
      const year = art.date?.split('-')[0] ?? 'Unknown';
      if (year !== currentYear) {
        groups.push({ year, articles: [art] });
        currentYear = year;
      } else {
        groups[groups.length - 1].articles.push(art);
      }
    });
    return groups;
  }, [articles]);

  const sliderIndex = sliderYears.indexOf(visibleYear);

  return (
    <div ref={containerRef} className="timeline-pane">
      {/* Mobile year slider — sticky at top */}
      {sliderYears.length > 0 && (
        <div className="timeline-slider-bar">
          <div className="timeline-slider-label">{visibleYear}</div>
          <input
            type="range"
            min={0}
            max={sliderYears.length - 1}
            value={Math.max(0, sliderIndex)}
            onChange={handleSliderChange}
            className="timeline-range-input"
          />
          <div className="timeline-slider-ticks">
            <span>{sliderYears[0]}</span>
            <span>{sliderYears[sliderYears.length - 1]}</span>
          </div>
        </div>
      )}

      {yearGroups.map((group) => (
        <div key={group.year}>
          <div
            className="timeline-year-header"
            data-year={group.year}
            ref={(el) => {
              if (el) yearHeaderRefs.current.set(group.year, el);
              else yearHeaderRefs.current.delete(group.year);
            }}
          >
            {group.year}
          </div>
          {group.articles.map((art) => {
            const isSelected = selectedArticle?.uuid === art.uuid;
            return (
              <div
                key={art.uuid}
                ref={(el) => {
                  if (el) itemRefs.current.set(art.uuid, el);
                  else itemRefs.current.delete(art.uuid);
                }}
                className={`timeline-item ${isSelected ? 'active' : ''}`}
                data-uuid={art.uuid}
              >
                {/* Clickable header */}
                <div
                  className="timeline-header"
                  onClick={() => handleHeaderClick(art)}
                >
                  <div style={{ flex: 1, minWidth: 0 }}>
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
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', marginLeft: 'auto', flexShrink: 0 }}>
                    <CopyLinkButton uuid={art.uuid} />
                    <PlayAudioButton uuid={art.uuid} title={art.title} />
                  </div>
                </div>

                {/* Expanded detail view — NOT clickable */}
                {isSelected && (() => {
                  if (bodies === null) { onNeedBodies(); }
                  const bodyHtml = bodies ? bodies[art.uuid] ?? '' : null;
                  return (
                  <div className="detail-view" onClick={(e) => e.stopPropagation()}>
                    {art.summary && (
                      <div className="detail-summary">
                        <div className="detail-summary-label">AI Summary</div>
                        <div className="detail-summary-text">{art.summary}</div>
                      </div>
                    )}
                    {bodyHtml === null ? (
                      <div className="detail-body" style={{ color: 'var(--text-dim)', fontStyle: 'italic' }}>
                        Loading…
                      </div>
                    ) : (
                    <div
                      className="detail-body"
                      dangerouslySetInnerHTML={{
                        __html: wikiLinkToHtml(bodyHtml, baseUrl),
                      }}
                    />
                    )}
                    {(art.player_impact || art.modern_impact) && (
                      <div className="detail-analysis">
                        <div className="detail-analysis-label">AI Analysis</div>
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
                    <TagList items={art.persons || []} color="var(--elite-blue)" baseUrl={baseUrl} />
                    <TagList items={art.groups || []} color="var(--elite-orange)" baseUrl={baseUrl} />
                    <TagList items={art.technologies || []} color="var(--elite-green)" baseUrl={baseUrl} />
                    <TagList items={art.entities || []} color="var(--elite-yellow)" baseUrl={baseUrl} />
                  </div>
                  );
                })()}
              </div>
            );
          })}
        </div>
      ))}
    </div>
  );
}
