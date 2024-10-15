import React, { useState, useEffect } from 'react';
import JSXParser from 'react-jsx-parser';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import BrowserOnly from '@docusaurus/BrowserOnly';

// Utility function to remove JSX tags in case of errors
const sanitizeJSX = (message) => {
  return message.replace(/<[^>]+>/g, ''); // Strips out all tags, leaving plain text
};

const API_BASE_URL =
  process.env.NODE_ENV === 'development'
    ? '/api/v1/vertex-genai'
    : 'https://vertex-genai-533923089340.europe-west1.run.app';

function MultivacChatMessage({ components, debug = false }) {
  const { siteConfig } = useDocusaurusContext();
  const [userInput, setUserInput] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [safeMessage, setSafeMessage] = useState(''); // For rendering fallback text

  const apiKey = siteConfig.customFields.multivacApiKey;

  useEffect(() => {
    return () => {
      setMessage('');
      setError(null);
      setLoading(false);
      setSafeMessage(''); // Cleanup
    };
  }, []);

  const fetchDummyData = async () => {
    setLoading(true);
    setError(null);
    setMessage('');

    try {
      await new Promise((resolve) => setTimeout(resolve, 2000));
      const dummyResponse = `This is normal markdown. <Highlight color="#c94435">This is a highlighted response</Highlight>. This is a CustomPlot component: <CustomPlot data={[{ x: [1, 2, 3, 4], y: [10, 15, 13, 17], type: 'scatter', mode: 'lines+markers' }]} />`;
      setMessage(dummyResponse);
    } catch (error) {
      setError('An error occurred while fetching data.');
    } finally {
      setLoading(false);
    }
  };

  const fetchRealData = async () => {
    setLoading(true);
    setError(null);
    setMessage('');

    if (!apiKey) {
      setError("Missing API key.");
      setLoading(false);
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/vac/streaming/dynamic_blog_mdx`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': apiKey,
        },
        body: JSON.stringify({ user_input: userInput, stream_only: true }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let done = false;

      while (!done) {
        const { value, done: doneReading } = await reader.read();
        done = doneReading;

        if (value) {
          const chunk = decoder.decode(value);
          try {
            const json = JSON.parse(chunk);
            console.log("Ignoring JSON chunk:", json);
          } catch (e) {
            setMessage((prev) => prev + chunk);
          }
        }
      }
    } catch (error) {
      setError(`An error occurred while fetching data: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (userInput.trim()) {
      if (debug) {
        fetchDummyData();
      } else {
        fetchRealData();
      }
    } else {
      setError('Input cannot be empty');
    }
  };

  const handleJSXError = () => {
    try {
      return (
        <JSXParser
          jsx={message}
          components={components}
          renderInWrapper={false}
          allowUnknownElements={false}
          blacklistedTags={['script', 'style', 'iframe', 'link', 'meta']}
          onError={(error) => console.error('onError parsing JSX:', error)} 
        />
      );
    } catch (err) {
      console.error('catch Error parsing JSX, attempting santize', sanitizeJSX(message));
      // Fallback to plain text if JSX parsing fails
      return <p>{sanitizeJSX(message)}</p>;
    }
  };

  return (
    <BrowserOnly>
      {() => (
        <div className="multivac-chat-container">
          <form onSubmit={handleSubmit}>
            <input
              type="text"
              placeholder="Ask a question..."
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              className="multivac-input"
            />
            <button type="submit" disabled={loading} className="multivac-submit-btn">
              {loading ? 'Loading...' : 'Submit'}
            </button>
          </form>

          {loading && <p>Fetching response...</p>}

          {error && <p className="error-message">{error}</p>}

          <div className="multivac-message-output">
            {message ? handleJSXError() : null}
          </div>
        </div>
      )}
    </BrowserOnly>
  );
}

export default MultivacChatMessage;