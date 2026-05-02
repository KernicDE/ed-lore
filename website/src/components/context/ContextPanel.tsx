import { useMemo } from 'react';

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

interface ContextPanelProps {
  currentDate: string;
  entities: Record<string, Entity>;
  arcs: Record<string, Arc>;
  visibleArticles: { arc_id: string | null; entities: string[]; groups: string[]; locations: string[]; topics: string[]; persons: string[]; technologies: string[] }[];
  allYears: string[];
  onYearSelect?: (year: string) => void;
}

function makeEid(name: string): string {
  return name
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/\s+/g, '-')
    .replace(/[^\w-]/g, '');
}

/** Exclude sentence-fragment false positives from entity extraction */
function isGarbageName(name: string): boolean {
  const lower = name.toLowerCase();
  const badPrefixes = [
    'a ', 'an ', 'the ', 'his ', 'her ', 'their ', 'our ', 'we ', 'it ',
    'this ', 'that ', 'these ', 'those ', 'authorities', 'spokesperson',
    'representative', 'observers', 'competitors', 'citizens', 'many ',
    'several ', 'hundreds', 'dozens', 'those ', 'these ', 'there ',
    'here ', 'when ', 'where ', 'why ', 'how ', 'what ', 'who ', 'which ',
    'under ', 'over ', 'into ', 'onto ', 'upon ', 'within ', 'without ',
    'across ', 'along ', 'around ', 'behind ', 'beside ', 'beyond ',
    'despite ', 'during ', 'except ', 'inside ', 'outside ', 'through ',
    'toward ', 'towards ', 'until ', 'via ', 'with ', 'within ', 'according ',
    'following ', 'regarding ', 'concerning ', 'considering ', 'including ',
    'assuming ', 'based ', 'according ', 'thanks ', 'due ', 'owing ', 'prior ',
    'subsequent ', 'regardless ', 'notwithstanding ', 'after ', 'before ',
    'since ', 'while ', 'whereas ', 'although ', 'though ', 'unless ', 'whether ',
    'because ', 'as ', 'once ', 'until ', 'till ', 'than ', 'then ', 'now ',
    'later ', 'soon ', 'earlier ', 'recently ', 'currently ', 'previously ',
    'originally ', 'initially ', 'finally ', 'eventually ', 'ultimately ',
    'suddenly ', 'gradually ', 'immediately ', 'shortly ', 'frequently ',
    'often ', 'sometimes ', 'rarely ', 'never ', 'always ', 'usually ',
    'generally ', 'typically ', 'normally ', 'commonly ', 'partly ',
    'mostly ', 'almost ', 'nearly ', 'approximately ', 'roughly ', 'about ',
    'exactly ', 'precisely ', 'specifically ', 'particularly ', 'especially ',
    'notably ', 'mainly ', 'primarily ', 'essentially ', 'basically ',
    'effectively ', 'potentially ', 'likely ', 'probably ', 'possibly ',
    'perhaps ', 'maybe ', 'certainly ', 'definitely ', 'absolutely ',
    'clearly ', 'obviously ', 'evidently ', 'apparently ', 'seemingly ',
    'presumably ', 'allegedly ', 'reportedly ', 'supposedly ', 'arguably ',
    'admittedly ', 'fortunately ', 'unfortunately ', 'luckily ', 'regrettably ',
    'sadly ', 'happily ', 'strangely ', 'oddly ', 'curiously ', 'interestingly ',
    'significantly ', 'importantly ', 'crucially ', 'vitally ', 'critically ',
    'seriously ', 'severely ', 'extremely ', 'highly ', 'strongly ', 'weakly ',
    'deeply ', 'greatly ', 'considerably ', 'substantially ', 'markedly ',
    'noticeably ', 'remarkably ', 'strikingly ', 'dramatically ', 'radically ',
    'fundamentally ', 'thoroughly ', 'completely ', 'totally ', 'entirely ',
    'fully ', 'wholly ', 'partly ', 'partially ', 'half ', 'quarter ',
    'third ', 'twice ', 'double ', 'triple ', 'single ', 'multiple ',
    'various ', 'several ', 'numerous ', 'countless ', 'infinite ', 'endless ',
    'limitless ', 'boundless ', 'vast ', 'huge ', 'massive ', 'enormous ',
    'immense ', 'gigantic ', 'colossal ', 'tremendous ', 'immense ', 'great ',
    'large ', 'big ', 'small ', 'tiny ', 'little ', 'miniature ', 'microscopic ',
    'short ', 'long ', 'brief ', 'extended ', 'lasting ', 'temporary ',
    'permanent ', 'constant ', 'continuous ', 'ongoing ', 'intermittent ',
    'sporadic ', 'occasional ', 'regular ', 'irregular ', 'frequent ',
    'infrequent ', 'periodic ', 'seasonal ', 'annual ', 'monthly ', 'weekly ',
    'daily ', 'hourly ', 'nightly ', 'weekly ', 'yearly ', 'decadal ',
  ];
  if (badPrefixes.some(p => lower.startsWith(p))) return true;
  if (/\b(in|of|to|from|at|on|with|by|for|about|into|onto|upon|within|without|across|along|around|behind|beside|beyond|despite|during|except|inside|outside|through|toward|towards|until|via|regarding|concerning|considering|including|according|following|thanks|due|owing|prior|subsequent|regardless|notwithstanding)\s+the\b/.test(name)) return true;
  return false;
}

function isQualityEntity(name: string, count: number): boolean {
  if (count < 2) return false;
  return !isGarbageName(name);
}

export default function ContextPanel({
  currentDate,
  entities,
  arcs,
  visibleArticles,
  allYears,
  onYearSelect,
}: ContextPanelProps) {
  const isUnlocked = (firstSeen: string | null | undefined) => {
    if (!firstSeen) return true;
    return firstSeen <= currentDate;
  };

  const activeArcs = useMemo(() => {
    const arcSet = new Set<string>();
    visibleArticles.forEach((a) => {
      if (a.arc_id) arcSet.add(a.arc_id);
    });
    return Array.from(arcSet)
      .map((id) => arcs[id])
      .filter(Boolean)
      .sort((a, b) => b.mention_count - a.mention_count);
  }, [visibleArticles, arcs, currentDate]);

  const contextEntities = useMemo(() => {
    const counts = new Map<string, number>();
    visibleArticles.forEach((a) => {
      [...a.persons, ...a.technologies, ...a.groups, ...a.locations].forEach((name) => {
        const eid = makeEid(name);
        counts.set(eid, (counts.get(eid) || 0) + 1);
      });
      a.entities.forEach((name) => {
        if (name.includes(' ')) return;
        const eid = makeEid(name);
        counts.set(eid, (counts.get(eid) || 0) + 1);
      });
    });
    return Array.from(counts.entries())
      .map(([eid, count]) => ({ ...entities[eid], count }))
      .filter((e) => e && e.id && isUnlocked(e.first_seen_date))
      .filter((e) => !isGarbageName(e.name))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10);
  }, [visibleArticles, entities, currentDate]);

  const currentYear = currentDate?.split('-')[0] || '';

  // Slider: left = past (oldest), right = present (newest)
  const sliderYears = useMemo(() => [...allYears].sort((a, b) => a.localeCompare(b)), [allYears]);
  const sliderIndex = sliderYears.indexOf(currentYear);

  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const idx = parseInt(e.target.value, 10);
    const year = sliderYears[idx];
    if (year) onYearSelect?.(year);
  };

  const entityTypeLabel: Record<string, string> = {
    person: 'P',
    faction: 'F',
    location: 'L',
    technology: 'T',
  };

  return (
    <div className="context-pane">
      {/* Year Slider */}
      {sliderYears.length > 0 && (
        <div className="holo-panel">
          <div className="holo-title">Jump to Year</div>
          <div style={{ padding: '10px 0' }}>
            <input
              type="range"
              min={0}
              max={sliderYears.length - 1}
              value={Math.max(0, sliderIndex)}
              onChange={handleSliderChange}
              className="year-range-input"
              aria-label="Jump to year"
              title="Jump to year"
              style={{
                width: '100%',
                height: 4,
                WebkitAppearance: 'none',
                appearance: 'none',
                background: 'var(--border-glow)',
                borderRadius: 2,
                outline: 'none',
                cursor: 'pointer',
              }}
            />
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                marginTop: 8,
                fontFamily: 'var(--font-mono)',
                fontSize: 10,
                color: 'var(--text-secondary)',
              }}
            >
              {sliderYears.map((year) => (
                <span
                  key={year}
                  style={{
                    color: year === currentYear ? 'var(--elite-orange)' : 'var(--text-secondary)',
                    fontWeight: year === currentYear ? 700 : 400,
                  }}
                >
                  {year.slice(-2)}
                </span>
              ))}
            </div>
            <div
              style={{
                textAlign: 'center',
                marginTop: 6,
                fontFamily: 'var(--font-hud)',
                fontSize: 14,
                color: 'var(--elite-orange)',
                letterSpacing: 2,
              }}
            >
              {currentYear || sliderYears[sliderYears.length - 1]}
            </div>
          </div>
        </div>
      )}

      {/* Related Arcs */}
      {activeArcs.length > 0 && (
        <div className="holo-panel blue">
          <div className="holo-title blue">Related Arcs</div>
          {activeArcs.map((arc) => (
            <a
              key={arc.id}
              href={`${(import.meta.env.BASE_URL || '').replace(/\/$/, '')}/arc/${arc.id}/`}
              style={{
                display: 'block',
                padding: '10px 0',
                borderBottom: '1px solid var(--border-default)',
                textDecoration: 'none',
                color: 'inherit',
              }}
            >
              <div style={{ fontSize: 15, fontWeight: 500, color: 'var(--text-primary)' }}>
                {arc.name}
              </div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-secondary)', marginTop: 2 }}>
                {arc.first_seen_date} → {arc.last_seen_date} · {arc.mention_count} articles
              </div>
            </a>
          ))}
        </div>
      )}

      {/* Context */}
      {contextEntities.length > 0 && (
        <div className="holo-panel">
          <div className="holo-title">Context</div>
          {contextEntities.map((fig) => {
            const classified = !isUnlocked(fig.first_seen_date);
            return (
              <a
                key={fig.id}
                href={`${(import.meta.env.BASE_URL || '').replace(/\/$/, '')}/entity/${fig.id}/`}
                className={`entity-card ${classified ? 'classified' : ''}`}
                style={{ textDecoration: 'none' }}
              >
                <div className={`entity-icon ${fig.type || 'person'}`}>
                  {entityTypeLabel[fig.type] || '?'}
                </div>
                <div style={{ minWidth: 0 }}>
                  <div className="entity-name">{fig.name}</div>
                  <div className="entity-meta">
                    {fig.first_seen_date} · {fig.count} mentions
                  </div>
                </div>
              </a>
            );
          })}
        </div>
      )}

      {activeArcs.length === 0 && contextEntities.length === 0 && (
        <div className="holo-panel" style={{ textAlign: 'center', padding: 40 }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 13, color: 'var(--text-secondary)' }}>
            No data for this period
          </div>
        </div>
      )}
    </div>
  );
}
