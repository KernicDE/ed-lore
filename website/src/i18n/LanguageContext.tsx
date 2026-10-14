import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import { t as translate, getLangFromDocument, type Lang } from './dict';

interface LanguageContextValue {
  lang: Lang;
  setLang: (lang: Lang) => void;
  t: (key: string, vars?: Record<string, string | number>) => string;
}

const STORAGE_KEY = 'galnet-lang';

/** Persist + broadcast a language change (same pattern as galnet-theme). */
export function setGlobalLang(lang: Lang): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, lang);
  } catch {
    // localStorage unavailable
  }
  document.documentElement.setAttribute('data-lang', lang);
  document.documentElement.setAttribute('lang', lang);
  window.dispatchEvent(new CustomEvent('galnet-lang-change', { detail: { lang } }));
}

/**
 * Standalone hook for React islands that live outside the LanguageProvider
 * tree (SearchIsland / EntityGraph on static pages). Reads <html data-lang>
 * and re-renders on changes, mirroring the MutationObserver pattern used for
 * data-theme / data-ai-mode.
 */
export function useLang(): Lang {
  const [lang, setLang] = useState<Lang>(getLangFromDocument);
  useEffect(() => {
    const observer = new MutationObserver(() => {
      setLang(getLangFromDocument());
    });
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-lang'] });
    return () => observer.disconnect();
  }, []);
  return lang;
}

const LanguageContext = createContext<LanguageContextValue | null>(null);

export function LanguageProvider({ children }: { children: ReactNode }) {
  const observed = useLang();
  const [lang, setLangState] = useState<Lang>(getLangFromDocument);

  // Keep provider state in sync when the attribute changes outside React
  // (e.g. LanguageToggle on a static page, or another tab).
  useEffect(() => {
    setLangState(getLangFromDocument());
  }, [observed]);

  const setLang = useCallback((next: Lang) => {
    setLangState(next);
    setGlobalLang(next);
  }, []);

  const t = useCallback((key: string, vars?: Record<string, string | number>) => translate(lang, key, vars), [lang]);

  return (
    <LanguageContext.Provider value={{ lang, setLang, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

/**
 * Language accessor for components. Works inside and outside the provider:
 * outside, it observes <html data-lang> directly.
 */
export function useLanguage(): LanguageContextValue {
  const ctx = useContext(LanguageContext);
  const observed = useLang();
  const t = useCallback((key: string, vars?: Record<string, string | number>) => translate(observed, key, vars), [observed]);
  if (!ctx) {
    return { lang: observed, setLang: setGlobalLang, t };
  }
  return ctx;
}
