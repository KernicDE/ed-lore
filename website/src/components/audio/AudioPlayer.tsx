import { useState, useRef, useEffect, useCallback } from 'react';
import { useLanguage } from '../../i18n/LanguageContext';
import type { Lang } from '../../i18n/dict';

interface Article {
  uuid: string;
  title: string;
  date: string;
  audio_hash?: string;
  has_audio?: boolean;
  audio_hash_de?: string;
  has_audio_de?: boolean;
  category?: string;
  source_type?: string;
}

interface AudioPlayerProps {
  article: Article | null;
}

const BASE = (import.meta.env.BASE_URL || '/').replace(/\/$/, '');

// Cloudflare R2 public bucket URL
const R2_AUDIO_BASE = 'https://pub-4404b20907c141e1b68f3dc578038230.r2.dev/audio';

function getAudioUrl(uuid: string, hash: string | undefined, lang: Lang): string {
  const suffix = hash ? `?v=${hash}` : '';
  if (R2_AUDIO_BASE) {
    return lang === 'de'
      ? `${R2_AUDIO_BASE}/de/${uuid}.mp3${suffix}`
      : `${R2_AUDIO_BASE}/${uuid}.mp3${suffix}`;
  }
  return lang === 'de'
    ? `${BASE}/audio/de/${uuid}.mp3${suffix}`
    : `${BASE}/audio/${uuid}.mp3${suffix}`;
}

const LOAD_TIMEOUT_MS = 20_000; // 20 seconds before showing error

export default function AudioPlayer({ article }: AudioPlayerProps) {
  const { t, lang } = useLanguage();
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [error, setError] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  // uuid of the article whose DE audio failed to load this session —
  // afterwards (and for articles without has_audio_de) we use English audio.
  const [deFailedFor, setDeFailedFor] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const rafRef = useRef<number>(0);
  const loadTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const wantDe = lang === 'de' && !!article?.has_audio_de && deFailedFor !== article?.uuid;
  const audioUrl = article
    ? getAudioUrl(
        article.uuid,
        wantDe ? (article.audio_hash_de ?? article.audio_hash) : article.audio_hash,
        wantDe ? 'de' : 'en',
      )
    : null;

  const catBadge = article?.category === 'galnet' ? t('badgeOfficial')
    : article?.category === 'chronicle' ? t('badgeChronicle')
    : article?.category === 'cmdr-log' ? t('badgeCmdrLog')
    : '';
  const catColor = article?.category === 'galnet' ? 'var(--elite-orange)'
    : article?.category === 'chronicle' ? 'var(--elite-blue)'
    : article?.category === 'cmdr-log' ? 'var(--elite-green)'
    : 'var(--text-dim)';

  // Stop playback when AI mode is turned off
  useEffect(() => {
    const observer = new MutationObserver(() => {
      const mode = document.documentElement.getAttribute('data-ai-mode');
      if (mode === 'off' && audioRef.current) {
        audioRef.current.pause();
        setIsPlaying(false);
      }
    });
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-ai-mode'] });
    return () => observer.disconnect();
  }, []);

  const clearLoadTimeout = useCallback(() => {
    if (loadTimeoutRef.current) {
      clearTimeout(loadTimeoutRef.current);
      loadTimeoutRef.current = null;
    }
  }, []);

  // Load and auto-play when article changes
  useEffect(() => {
    setIsPlaying(false);
    setCurrentTime(0);
    setDuration(0);
    setError(false);
    setIsLoading(false);
    clearLoadTimeout();

    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.src = '';
      audioRef.current = null;
    }
    if (rafRef.current) {
      cancelAnimationFrame(rafRef.current);
    }

    if (!audioUrl) return;

    setIsLoading(true);
    loadTimeoutRef.current = setTimeout(() => {
      setIsLoading(false);
      setError(true);
      setIsPlaying(false);
    }, LOAD_TIMEOUT_MS);

    const audio = new Audio(audioUrl);
    audioRef.current = audio;

    audio.addEventListener('loadedmetadata', () => {
      setDuration(audio.duration || 0);
    });

    audio.addEventListener('ended', () => {
      setIsPlaying(false);
      setCurrentTime(0);
    });

    audio.addEventListener('error', () => {
      // DE audio missing/stale (e.g. not uploaded yet) — retry with English
      if (wantDe && article) {
        setDeFailedFor(article.uuid);
        return;
      }
      clearLoadTimeout();
      setIsLoading(false);
      setError(true);
      setIsPlaying(false);
    });

    audio.addEventListener('canplay', () => {
      clearLoadTimeout();
      setIsLoading(false);
      setError(false);
    });

    audio.play().then(() => {
      clearLoadTimeout();
      setIsPlaying(true);
      setIsLoading(false);
      setError(false);
      rafRef.current = requestAnimationFrame(updateTime);
    }).catch(() => {
      clearLoadTimeout();
      setIsLoading(false);
      setError(true);
    });
  }, [article?.uuid, audioUrl]);

  const updateTime = useCallback(() => {
    if (audioRef.current) {
      setCurrentTime(audioRef.current.currentTime);
      if (audioRef.current.duration && !isNaN(audioRef.current.duration)) {
        setDuration(audioRef.current.duration);
      }
    }
    rafRef.current = requestAnimationFrame(updateTime);
  }, []);

  const togglePlay = useCallback(async () => {
    if (!audioUrl) return;

    if (!audioRef.current) {
      setIsLoading(true);
      loadTimeoutRef.current = setTimeout(() => {
        setIsLoading(false);
        setError(true);
        setIsPlaying(false);
      }, LOAD_TIMEOUT_MS);

      const audio = new Audio(audioUrl);
      audioRef.current = audio;

      audio.addEventListener('loadedmetadata', () => {
        setDuration(audio.duration || 0);
      });

      audio.addEventListener('ended', () => {
        setIsPlaying(false);
        setCurrentTime(0);
      });

      audio.addEventListener('error', () => {
        if (wantDe && article) {
          setDeFailedFor(article.uuid);
          return;
        }
        clearLoadTimeout();
        setIsLoading(false);
        setError(true);
        setIsPlaying(false);
      });

      audio.addEventListener('canplay', () => {
        clearLoadTimeout();
        setIsLoading(false);
        setError(false);
      });
    }

    const audio = audioRef.current;

    if (isPlaying) {
      audio.pause();
      setIsPlaying(false);
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    } else {
      try {
        await audio.play();
        clearLoadTimeout();
        setIsPlaying(true);
        setIsLoading(false);
        setError(false);
        rafRef.current = requestAnimationFrame(updateTime);
      } catch (e) {
        clearLoadTimeout();
        setIsLoading(false);
        setError(true);
      }
    }
  }, [audioUrl, isPlaying, updateTime, clearLoadTimeout, wantDe, article]);

  useEffect(() => {
    return () => {
      clearLoadTimeout();
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, [clearLoadTimeout]);

  const formatTime = (t: number) => {
    if (!isFinite(t) || isNaN(t)) return '00:00';
    const m = Math.floor(t / 60);
    const s = Math.floor(t % 60);
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  if (!article) return null;

  return (
    <div className="audio-player ai-content">
      <button
        onClick={togglePlay}
        className="audio-play-btn"
        title={isPlaying ? t('pause') : t('play')}
        disabled={error && !isLoading}
      >
        {isLoading ? '◌' : isPlaying ? '⏸' : '▶'}
      </button>
      <div className="audio-info">
        <div className="audio-title" title={article.title}>
          {catBadge && (
            <span style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 9,
              color: catColor,
              border: `1px solid ${catColor}`,
              padding: '0 4px',
              marginRight: 6,
              opacity: 0.8,
              verticalAlign: 'middle',
            }}>
              {catBadge}
            </span>
          )}
          {article.title.length > 30 ? article.title.slice(0, 28) + '…' : article.title}
        </div>
        <div className="audio-time">
          {isLoading ? (
            <span style={{ color: 'var(--text-secondary)' }}>{t('loadingAudio')}</span>
          ) : error ? (
            <span style={{ color: 'var(--elite-red)' }}>{t('audioNotAvailable')}</span>
          ) : (
            <>
              {formatTime(currentTime)} / {formatTime(duration)}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
