import React, { useState, useEffect } from 'react';
import JSXParser from 'react-jsx-parser';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import BrowserOnly from '@docusaurus/BrowserOnly';

function MultivacChatMessage({ components, debug = false }) {
  const { siteConfig } = useDocusaurusContext();
  const [userInput, setUserInput] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const apiKey = siteConfig.customFields.multivacApiKey; 

  useEffect(() => {
    return () => {
      // Cleanup to avoid memory leaks
      setMessage('');
      setError(null);
      setLoading(false);
    };
  }, []);

  // Function to simulate the delayed dummy response (for debug mode)
  const fetchDummyData = async () => {
    setLoading(true);
    setError(null); // Clear previous errors
    setMessage('');  // Clear previous messages

    try {
      // Simulate a 2-second delay before returning dummy data
      await new Promise((resolve) => setTimeout(resolve, 2000));

      // Dummy response (replace this with any JSX content you want to test)
      const dummyResponse = `This is normal markdown. <Highlight color="#c94435">This is a highlighted response</Highlight>. This is a CustomPlot component:
      <CustomPlot data={[
          { x: [1, 2, 3, 4], y: [10, 15, 13, 17], type: 'scatter', mode: 'lines+markers' }
      ]} />
      `;

      // Set the dummy response in the message state
      setMessage(dummyResponse);
    } catch (error) {
      setError('An error occurred while fetching data.');
    } finally {
      setLoading(false);
    }
  };

  // Function to call the real API
  const fetchRealData = async () => {
    setLoading(true);
    setError(null); // Clear previous errors
    setMessage('');  // Clear previous messages

    // Check if the API key is undefined
    if (!apiKey) {
      setError("Missing API key. Please ensure the 'REACT_APP_MULTIVAC_API_KEY' environment variable is set.");
      setLoading(false);
      return;
    }

    try {
      const response = await fetch('/api/v1/vertex-genai/vac/streaming/dynamic_blog_mdx', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': apiKey, // Ensure to set the API key in your environment variables
        },
        body: JSON.stringify({
          user_input: userInput
        }),
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
          setMessage((prev) => prev + chunk);
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
        fetchDummyData(); // Fetch the dummy response in debug mode
      } else {
        fetchRealData(); // Call the real API when debug mode is off
      }
    } else {
      setError('Input cannot be empty');
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
            <JSXParser
              jsx={message}
              components={components} // Pass components dynamically
              renderInWrapper={false}
              allowUnknownElements={false}
              blacklistedTags={['script', 'style', 'iframe', 'link', 'meta']}
            />
          </div>
        </div>
      )}
    </BrowserOnly>
  );
}

export default MultivacChatMessage;