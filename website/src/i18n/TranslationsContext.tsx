import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { useLanguage } from './LanguageContext';

// German content translations (Phase 2 data shape). Only non-empty fields are
// present per record; consumers fall back to the English field per field.
export interface ArticleTranslations {
  summary_de?: string;
  player_impact_de?: string;
  modern_impact_de?: string;
}

export interface EntityTranslations {
  bio_de?: string;
}

export interface ArcTranslations {
  description_de?: string;
  summary_de?: string;
  outcome_de?: string;
}

export interface TranslationsData {
  articles: Record<string, ArticleTranslations>;
  entities: Record<string, EntityTranslations>;
  arcs: Record<string, ArcTranslations>;
}

const EMPTY: TranslationsData = { articles: {}, entities: {}, arcs: {} };

const TranslationsContext = createContext<TranslationsData>(EMPTY);

const BASE = (import.meta.env.BASE_URL || '/').replace(/\/$/, '');

// Module-level promise: the file is fetched at most once per session, no
// matter how often the language is toggled.
let translationsPromise: Promise<TranslationsData> | null = null;

function loadTranslations(): Promise<TranslationsData> {
  if (!translationsPromise) {
    const cacheBuster = typeof window !== 'undefined' && (window as any).GALNET_BUILD
      ? `?v=${encodeURIComponent((window as any).GALNET_BUILD)}`
      : `?t=${Date.now()}`;
    translationsPromise = fetch(`${BASE}/data/translations-de.json${cacheBuster}`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((data: Partial<TranslationsData>) => ({
        articles: data.articles || {},
        entities: data.entities || {},
        arcs: data.arcs || {},
      }))
      .catch((err) => {
        console.warn('[i18n] Failed to load German translations, using English only:', err);
        return EMPTY;
      });
  }
  return translationsPromise;
}

/**
 * Provides the German content translations. Fetches lazily the first time the
 * active language is 'de'; later switches apply the already-loaded data
 * instantly. Fetch failure resolves to empty maps (pure English).
 */
export function TranslationsProvider({ children }: { children: ReactNode }) {
  const { lang } = useLanguage();
  const [de, setDe] = useState<TranslationsData>(EMPTY);

  useEffect(() => {
    if (lang !== 'de') return;
    let cancelled = false;
    loadTranslations().then((data) => {
      if (!cancelled) setDe(data);
    });
    return () => {
      cancelled = true;
    };
  }, [lang]);

  return (
    <TranslationsContext.Provider value={de}>
      {children}
    </TranslationsContext.Provider>
  );
}

/** German content translations; empty maps until (and unless) loaded. */
export function useTranslations(): TranslationsData {
  return useContext(TranslationsContext);
}
