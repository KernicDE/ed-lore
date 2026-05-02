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

export default function AudioPlayer({ article }: AudioPlayerProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const rafRef = useRef<number>(0);

  const audioUrl = article ? `${BASE}/audio/${article.uuid}.mp3` : null;

  // Load and auto-play when article changes
  useEffect(() => {
    setIsPlaying(false);
    setCurrentTime(0);
    setDuration(0);
    setError(null);
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.src = '';
      audioRef.current = null;
    }
    if (rafRef.current) {
      cancelAnimationFrame(rafRef.current);
    }

    if (!audioUrl) return;

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
      setError('Audio not available');
      setIsPlaying(false);
    });

    audio.addEventListener('canplay', () => {
      setError(null);
    });

    audio.play().then(() => {
      setIsPlaying(true);
      setError(null);
      rafRef.current = requestAnimationFrame(updateTime);
    }).catch(() => {
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
        setError('Audio not available');
        setIsPlaying(false);
      });

      audio.addEventListener('canplay', () => {
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
        setIsPlaying(true);
        setError(null);
        rafRef.current = requestAnimationFrame(updateTime);
      } catch (e) {
        setError('Audio not available');
      }
    }
  }, [audioUrl, isPlaying, updateTime]);

  useEffect(() => {
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, []);

  const formatTime = (t: number) => {
    if (!isFinite(t) || isNaN(t)) return '00:00';
    const m = Math.floor(t / 60);
    const s = Math.floor(t % 60);
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  if (!article) {
    return (
      <div className="audio-player">
        <span style={{ fontSize: 11, color: 'var(--text-secondary)' }}>Click ▶ Audio on an article to play</span>
      </div>
    );
  }

  return (
    <div className="audio-player">
      <button
        onClick={togglePlay}
        className="audio-play-btn"
        title={isPlaying ? 'Pause' : 'Play'}
        disabled={!!error}
      >
        {isPlaying ? '⏸' : '▶'}
      </button>
      <div className="audio-info">
        <div className="audio-title" title={article.title}>
          {article.title.length > 30 ? article.title.slice(0, 28) + '…' : article.title}
        </div>
        <div className="audio-time">
          {error ? (
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
