/**
 * Displays narration text for the current demo step
 * Supports text-to-speech and highlighting
 */

import React, { useState, useEffect } from 'react';
import { Box, Paper, Typography } from '@mui/material';

interface DemoNarrationProps {
  narration: string;
  isPlaying: boolean;
}

export const DemoNarration: React.FC<DemoNarrationProps> = ({ narration, isPlaying }) => {
  const [highlightedText, setHighlightedText] = useState('');

  useEffect(() => {
    if (isPlaying) {
      // Simulate progressive text reveal
      let currentIndex = 0;
      const interval = setInterval(() => {
        if (currentIndex <= narration.length) {
          setHighlightedText(narration.substring(0, currentIndex));
          currentIndex += 2;
        } else {
          clearInterval(interval);
        }
      }, 30);

      return () => clearInterval(interval);
    } else {
      setHighlightedText(narration);
    }
  }, [narration, isPlaying]);

  return (
    <Paper
      variant="outlined"
      sx={{
        p: 2,
        bgcolor: 'primary.50',
        borderColor: 'primary.main',
        borderWidth: 2,
        position: 'relative'
      }}
    >
      <Box>
        <Typography
          variant="body1"
          sx={{
            lineHeight: 1.8,
            color: 'text.primary',
            fontFamily: 'Georgia, serif',
            fontSize: '1.05rem'
          }}
        >
          {highlightedText}
          {isPlaying && highlightedText.length < narration.length && (
            <span
              style={{
                display: 'inline-block',
                width: '2px',
                height: '1.2em',
                backgroundColor: 'currentColor',
                marginLeft: '2px',
                animation: 'blink 1s infinite'
              }}
            />
          )}
        </Typography>
      </Box>
      <style>
        {`
          @keyframes blink {
            0%, 50% { opacity: 1; }
            51%, 100% { opacity: 0; }
          }
        `}
      </style>
    </Paper>
  );
};
