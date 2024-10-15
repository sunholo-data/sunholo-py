import React from 'react';
import '@site/src/css/custom.css';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPodcast } from '@fortawesome/free-solid-svg-icons';


const AudioPlayer = ({ src }) => {
    return (
        <div className="audio-player-container">
          <div className="audio-header">
            <FontAwesomeIcon icon={faPodcast} className="icon" />
            <p className="audio-description">
              Listen to a <a href='https://notebooklm.google/' target="_blank">NotebookLM</a> generated podcast about this blogpost:
            </p>
          </div>
          <audio controls className="custom-audio">
            <source src={src} type="audio/mpeg" />
            Your browser does not support the audio element.
          </audio>
          <p className="alt-link">
            <a href={src} target="_blank" rel="noopener noreferrer">
              Alternatively, listen to the audio file directly
            </a>
          </p>
        </div>
      );
};

export default AudioPlayer;