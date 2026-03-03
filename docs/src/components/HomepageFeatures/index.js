import clsx from 'clsx';
import Heading from '@theme/Heading';
import Link from '@docusaurus/Link';
import styles from './styles.module.css';

function MultiProviderDiagram() {
  return (
    <svg viewBox="0 0 320 200" className={styles.featureSvg} xmlns="http://www.w3.org/2000/svg">
      {/* Center node */}
      <rect x="110" y="75" width="100" height="50" rx="8" fill="#c94435" />
      <text x="160" y="105" textAnchor="middle" fill="white" fontSize="14" fontWeight="bold">sunholo</text>

      {/* Provider nodes */}
      <rect x="10" y="10" width="80" height="32" rx="6" fill="#4285F4" />
      <text x="50" y="31" textAnchor="middle" fill="white" fontSize="11">Gemini</text>

      <rect x="120" y="10" width="80" height="32" rx="6" fill="#10A37F" />
      <text x="160" y="31" textAnchor="middle" fill="white" fontSize="11">OpenAI</text>

      <rect x="230" y="10" width="80" height="32" rx="6" fill="#D4A574" />
      <text x="270" y="31" textAnchor="middle" fill="white" fontSize="11">Anthropic</text>

      <rect x="40" y="160" width="70" height="32" rx="6" fill="#666" />
      <text x="75" y="181" textAnchor="middle" fill="white" fontSize="11">Ollama</text>

      <rect x="210" y="160" width="70" height="32" rx="6" fill="#0078D4" />
      <text x="245" y="181" textAnchor="middle" fill="white" fontSize="11">Azure</text>

      {/* Config file */}
      <rect x="120" y="160" width="80" height="32" rx="6" fill="#2E7D32" />
      <text x="160" y="181" textAnchor="middle" fill="white" fontSize="10">config.yaml</text>

      {/* Connecting lines */}
      <line x1="50" y1="42" x2="130" y2="75" stroke="#888" strokeWidth="1.5" strokeDasharray="4,3" />
      <line x1="160" y1="42" x2="160" y2="75" stroke="#888" strokeWidth="1.5" strokeDasharray="4,3" />
      <line x1="270" y1="42" x2="190" y2="75" stroke="#888" strokeWidth="1.5" strokeDasharray="4,3" />
      <line x1="75" y1="160" x2="130" y2="125" stroke="#888" strokeWidth="1.5" strokeDasharray="4,3" />
      <line x1="160" y1="160" x2="160" y2="125" stroke="#888" strokeWidth="1.5" strokeDasharray="4,3" />
      <line x1="245" y1="160" x2="190" y2="125" stroke="#888" strokeWidth="1.5" strokeDasharray="4,3" />
    </svg>
  );
}

function AgentFrameworksDiagram() {
  return (
    <svg viewBox="0 0 320 200" className={styles.featureSvg} xmlns="http://www.w3.org/2000/svg">
      {/* Input frameworks */}
      <rect x="10" y="20" width="80" height="32" rx="6" fill="#4285F4" />
      <text x="50" y="41" textAnchor="middle" fill="white" fontSize="11">ADK</text>

      <rect x="10" y="65" width="80" height="32" rx="6" fill="#2E7D32" />
      <text x="50" y="86" textAnchor="middle" fill="white" fontSize="11">LangChain</text>

      <rect x="10" y="110" width="80" height="32" rx="6" fill="#7B1FA2" />
      <text x="50" y="131" textAnchor="middle" fill="white" fontSize="11">LlamaIndex</text>

      {/* Center node */}
      <rect x="120" y="55" width="80" height="50" rx="8" fill="#c94435" />
      <text x="160" y="80" textAnchor="middle" fill="white" fontSize="12" fontWeight="bold">sunholo</text>
      <text x="160" y="95" textAnchor="middle" fill="white" fontSize="9">.agents</text>

      {/* Output protocols */}
      <rect x="230" y="10" width="80" height="32" rx="6" fill="#E65100" />
      <text x="270" y="31" textAnchor="middle" fill="white" fontSize="11">FastAPI</text>

      <rect x="230" y="55" width="80" height="32" rx="6" fill="#0D47A1" />
      <text x="270" y="76" textAnchor="middle" fill="white" fontSize="11">MCP</text>

      <rect x="230" y="100" width="80" height="32" rx="6" fill="#1565C0" />
      <text x="270" y="121" textAnchor="middle" fill="white" fontSize="11">A2A</text>

      <rect x="230" y="145" width="80" height="32" rx="6" fill="#546E7A" />
      <text x="270" y="166" textAnchor="middle" fill="white" fontSize="11">Streaming</text>

      {/* Connecting lines - left */}
      <line x1="90" y1="36" x2="120" y2="70" stroke="#888" strokeWidth="1.5" strokeDasharray="4,3" />
      <line x1="90" y1="81" x2="120" y2="80" stroke="#888" strokeWidth="1.5" strokeDasharray="4,3" />
      <line x1="90" y1="126" x2="120" y2="90" stroke="#888" strokeWidth="1.5" strokeDasharray="4,3" />

      {/* Connecting lines - right */}
      <line x1="200" y1="70" x2="230" y2="26" stroke="#888" strokeWidth="1.5" strokeDasharray="4,3" />
      <line x1="200" y1="75" x2="230" y2="71" stroke="#888" strokeWidth="1.5" strokeDasharray="4,3" />
      <line x1="200" y1="85" x2="230" y2="116" stroke="#888" strokeWidth="1.5" strokeDasharray="4,3" />
      <line x1="200" y1="90" x2="230" y2="161" stroke="#888" strokeWidth="1.5" strokeDasharray="4,3" />
    </svg>
  );
}

function CloudInfraDiagram() {
  return (
    <svg viewBox="0 0 320 200" className={styles.featureSvg} xmlns="http://www.w3.org/2000/svg">
      {/* Center node */}
      <rect x="120" y="75" width="80" height="50" rx="8" fill="#c94435" />
      <text x="160" y="100" textAnchor="middle" fill="white" fontSize="12" fontWeight="bold">sunholo</text>
      <text x="160" y="115" textAnchor="middle" fill="white" fontSize="9">.database</text>

      {/* Cloud services */}
      <rect x="10" y="10" width="90" height="32" rx="6" fill="#4285F4" />
      <text x="55" y="31" textAnchor="middle" fill="white" fontSize="10">Cloud Run</text>

      <rect x="115" y="10" width="90" height="32" rx="6" fill="#0D47A1" />
      <text x="160" y="31" textAnchor="middle" fill="white" fontSize="10">AlloyDB</text>

      <rect x="220" y="10" width="90" height="32" rx="6" fill="#2E7D32" />
      <text x="265" y="31" textAnchor="middle" fill="white" fontSize="10">Pub/Sub</text>

      <rect x="20" y="160" width="80" height="32" rx="6" fill="#E65100" />
      <text x="60" y="181" textAnchor="middle" fill="white" fontSize="10">Firestore</text>

      <rect x="120" y="160" width="80" height="32" rx="6" fill="#7B1FA2" />
      <text x="160" y="181" textAnchor="middle" fill="white" fontSize="10">LanceDB</text>

      <rect x="220" y="160" width="80" height="32" rx="6" fill="#546E7A" />
      <text x="260" y="181" textAnchor="middle" fill="white" fontSize="10">Supabase</text>

      {/* Connecting lines */}
      <line x1="55" y1="42" x2="130" y2="75" stroke="#888" strokeWidth="1.5" strokeDasharray="4,3" />
      <line x1="160" y1="42" x2="160" y2="75" stroke="#888" strokeWidth="1.5" strokeDasharray="4,3" />
      <line x1="265" y1="42" x2="190" y2="75" stroke="#888" strokeWidth="1.5" strokeDasharray="4,3" />
      <line x1="60" y1="160" x2="130" y2="125" stroke="#888" strokeWidth="1.5" strokeDasharray="4,3" />
      <line x1="160" y1="160" x2="160" y2="125" stroke="#888" strokeWidth="1.5" strokeDasharray="4,3" />
      <line x1="260" y1="160" x2="190" y2="125" stroke="#888" strokeWidth="1.5" strokeDasharray="4,3" />
    </svg>
  );
}

const FeatureList = [
  {
    title: 'Multi-Provider GenAI',
    Diagram: MultiProviderDiagram,
    link: '/docs/integrations',
    description: (
      <>
        Use Google Gemini, OpenAI, Anthropic, Ollama and more through a unified
        config-driven interface. Swap models via YAML, not code.
      </>
    ),
  },
  {
    title: 'Agent Frameworks',
    Diagram: AgentFrameworksDiagram,
    link: '/docs/agents',
    description: (
      <>
        Build agents with Google ADK, LangChain, or LlamaIndex. Deploy as
        FastAPI services with built-in streaming, MCP, and A2A protocol support.
      </>
    ),
  },
  {
    title: 'Cloud-Ready Infrastructure',
    Diagram: CloudInfraDiagram,
    link: '/docs/databases',
    description: (
      <>
        Deploy to GCP Cloud Run with AlloyDB vectorstores, Pub/Sub messaging,
        and Firestore. Config-driven architecture scales from prototype to production.
      </>
    ),
  },
];

function Feature({Diagram, title, description, link}) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center">
        <Diagram />
      </div>
      <div className="text--center padding-horiz--md">
        <Heading as="h3">
          <Link to={link} className={styles.featureLink}>{title}</Link>
        </Heading>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures() {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}
