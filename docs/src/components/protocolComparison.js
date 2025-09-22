import React, { useState } from 'react';
import styles from './protocolComparison.module.css';

const ProtocolComparison = ({ 
  title = "Protocol Comparison",
  mode = "timeline", 
  items = [],
  showLegend = true 
}) => {
  const [activeView, setActiveView] = useState(mode === 'stats' ? 'timeline' : mode);
  const [selectedItem, setSelectedItem] = useState(null);

  // Timeline View Component
  const TimelineView = () => (
    <div className={styles.timeline}>
      <div className={styles.timelineLine}></div>
      {items.filter(item => !item.hideInTimeline).map((item, index) => (
        <div 
          key={index} 
          className={`${styles.timelineItem} ${index % 2 === 0 ? styles.left : styles.right}`}
          onClick={() => setSelectedItem(item)}
          style={{ '--item-color': item.color || '#0066cc' }}
          title="Click for more details"
        >
          <div className={styles.timelineNode}></div>
          <div className={styles.timelineContent}>
            <h3>{item.name}</h3>
            {item.year && <span className={styles.year}>{item.year}</span>}
            {item.description && (
              <p className={styles.timelineDescription}>
                {item.description}
              </p>
            )}
            {item.stats && item.stats.adoption && (
              <div className={styles.badge}>
                {item.stats.adoption}
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );

  // Comparison Cards View
  const ComparisonView = () => (
    <div className={styles.comparison}>
      {items.filter(item => !item.hideInComparison).map((item, index) => (
        <div 
          key={index} 
          className={styles.card}
          style={{ 
            borderTop: `4px solid ${item.color || '#0066cc'}`,
            flex: `1 1 ${100/items.filter(i => !i.hideInComparison).length}%`
          }}
        >
          <h3 className={styles.cardTitle}>{item.name}</h3>
          {item.year && (
            <div className={styles.cardYear}>{item.year}</div>
          )}
          
          {item.features && (
            <div className={styles.cardSection}>
              <h4>Features</h4>
              <ul className={styles.cardFeatures}>
                {item.features.map((feature, fi) => (
                  <li key={fi}>
                    <span className={styles.checkmark}>✓</span>
                    {feature}
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          {item.pros && (
            <div className={styles.cardSection}>
              <h4>Advantages</h4>
              <ul className={styles.pros}>
                {item.pros.map((pro, pi) => (
                  <li key={pi}>{pro}</li>
                ))}
              </ul>
            </div>
          )}
          
          {item.cons && (
            <div className={styles.cardSection}>
              <h4>Considerations</h4>
              <ul className={styles.cons}>
                {item.cons.map((con, ci) => (
                  <li key={ci}>{con}</li>
                ))}
              </ul>
            </div>
          )}
          
          {item.stats && (
            <div className={styles.statsGrid}>
              {Object.entries(item.stats).map(([key, value]) => (
                <div key={key} className={styles.stat}>
                  <span className={styles.statLabel}>{key}:</span>
                  <span className={styles.statValue}>{value}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );


  // View switcher buttons
  const ViewSwitcher = () => (
    <div className={styles.viewSwitcher}>
      <button 
        className={activeView === 'timeline' ? styles.active : ''}
        onClick={() => setActiveView('timeline')}
      >
        📅 Timeline
      </button>
      <button 
        className={activeView === 'comparison' ? styles.active : ''}
        onClick={() => setActiveView('comparison')}
      >
        🔀 Compare
      </button>
    </div>
  );

  // Legend component
  const Legend = () => (
    <div className={styles.legend}>
      {items.map((item, index) => (
        <span key={index} className={styles.legendItem}>
          <span 
            className={styles.legendColor} 
            style={{ backgroundColor: item.color || '#0066cc' }}
          ></span>
          {item.name}
        </span>
      ))}
    </div>
  );

  return (
    <div className={styles.container}>
      {title && <h2 className={styles.title}>{title}</h2>}
      
      <ViewSwitcher />
      
      <div className={styles.content}>
        {activeView === 'timeline' && <TimelineView />}
        {activeView === 'comparison' && <ComparisonView />}
      </div>
      
      {showLegend && items.length > 1 && <Legend />}
      
      {selectedItem && (
        <div className={styles.modal} onClick={() => setSelectedItem(null)}>
          <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
            <button className={styles.closeButton} onClick={() => setSelectedItem(null)}>×</button>
            <div>
              <h3>{selectedItem.name}</h3>
              {selectedItem.year && (
                <div className={styles.modalYear}>
                  <strong>Year:</strong> {selectedItem.year}
                </div>
              )}
              {selectedItem.description && (
                <p className={styles.modalDescription}>{selectedItem.description}</p>
              )}
              {selectedItem.features && selectedItem.features.length > 0 && (
                <div className={styles.modalFeatures}>
                  <h4>Features:</h4>
                  <ul>
                    {selectedItem.features.map((feature, fi) => (
                      <li key={fi}>{feature}</li>
                    ))}
                  </ul>
                </div>
              )}
              {selectedItem.stats && Object.keys(selectedItem.stats).length > 0 && (
                <div className={styles.modalStats}>
                  <h4>Statistics:</h4>
                  <div className={styles.modalStatsGrid}>
                    {Object.entries(selectedItem.stats).map(([key, value]) => (
                      <div key={key} className={styles.modalStat}>
                        <span className={styles.modalStatKey}>{key}:</span>
                        <span className={styles.modalStatValue}> {value}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {selectedItem.details && (
                <div className={styles.modalDetails}>
                  <h4>Details:</h4>
                  <p>{selectedItem.details}</p>
                </div>
              )}
              {selectedItem.links && selectedItem.links.length > 0 && (
                <div className={styles.modalLinks}>
                  <h4>Learn More:</h4>
                  <ul className={styles.linksList}>
                    {selectedItem.links.map((link, li) => (
                      <li key={li}>
                        <a href={link.url} target="_blank" rel="noopener noreferrer">
                          {link.title}
                        </a>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProtocolComparison;