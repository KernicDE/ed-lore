import { useState, useRef, useEffect, useCallback } from 'react';

interface Article {
  uuid: string;
  title: string;
  date: string;
}

interface AudioPlayerProps {
  article: Article | null;
}

const BASE = (import.meta.env.BASE_URL || '/').replace(/\/$/, '');

// Cloudflare R2 public bucket URL
const R2_AUDIO_BASE = 'https://pub-4404b20907c141e1b68f3dc578038230.r2.dev/audio';

function getAudioUrl(uuid: string): string {
  if (R2_AUDIO_BASE) {
    return `${R2_AUDIO_BASE}/${uuid}.mp3`;
  }
  return `${BASE}/audio/${uuid}.mp3`;
}

const LOAD_TIMEOUT_MS = 20_000; // 20 seconds before showing error

export default function AudioPlayer({ article }: AudioPlayerProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const rafRef = useRef<number>(0);
  const loadTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const audioUrl = article ? getAudioUrl(article.uuid) : null;

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
    setError(null);
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
      setError('Audio not available');
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
      clearLoadTimeout();
      setIsLoading(false);
      setError('Audio not available');
      setIsPlaying(false);
    });

    audio.addEventListener('canplay', () => {
      clearLoadTimeout();
      setIsLoading(false);
      setError(null);
    });

    audio.play().then(() => {
      clearLoadTimeout();
      setIsPlaying(true);
      setIsLoading(false);
      setError(null);
      rafRef.current = requestAnimationFrame(updateTime);
    }).catch(() => {
      clearLoadTimeout();
      setIsLoading(false);
      setError('Audio not available');
    });
  }, [article?.uuid]);

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
        setError('Audio not available');
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
        clearLoadTimeout();
        setIsLoading(false);
        setError('Audio not available');
        setIsPlaying(false);
      });

      audio.addEventListener('canplay', () => {
        clearLoadTimeout();
        setIsLoading(false);
        setError(null);
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
        setError(null);
        rafRef.current = requestAnimationFrame(updateTime);
      } catch (e) {
        clearLoadTimeout();
        setIsLoading(false);
        setError('Audio not available');
      }
    }
  }, [audioUrl, isPlaying, updateTime, clearLoadTimeout]);

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
    <div className="audio-player">
      <button
        onClick={togglePlay}
        className="audio-play-btn"
        title={isPlaying ? 'Pause' : 'Play'}
        disabled={!!error && !isLoading}
      >
        {isLoading ? '◌' : isPlaying ? '⏸' : '▶'}
      </button>
      <div className="audio-info">
        <div className="audio-title" title={article.title}>
          {article.title.length > 30 ? article.title.slice(0, 28) + '…' : article.title}
        </div>
        <div className="audio-time">
          {isLoading ? (
            <span style={{ color: 'var(--text-secondary)' }}>Loading audio…</span>
          ) : error ? (
            <span style={{ color: 'var(--elite-red)' }}>{error}</span>
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
