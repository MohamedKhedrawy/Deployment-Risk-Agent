import React, { useState } from 'react';
import Header from './components/Header';
import LeftPanel from './components/LeftPanel';
import RightPanel from './components/RightPanel';
import { analyzeFeature } from './api';

export default function App() {
  const [analysisState, setAnalysisState] = useState('idle'); // 'idle' | 'loading' | 'result'
  const [featureInput, setFeatureInput] = useState('');
  const [resultData, setResultData] = useState(null);

  const triggerAnalysis = (featureText) => {
    if (!featureText || !featureText.trim()) return;
    setFeatureInput(featureText);
    setAnalysisState('loading');
    setResultData(null);
    // The actual API call is handled inside LoadingState to synchronize with the animation timer.
    // We pass `featureText` to LoadingState so it can fetch the data.
  };

  return (
    <div style={{
      display: 'grid',
      gridTemplateRows: 'auto 1fr',
      height: '100vh',
      width: '100vw',
      overflow: 'hidden',
      background: 'var(--bg-base)'
    }}>
      <Header />
      
      <div style={{
        display: 'flex',
        height: '100%',
        overflow: 'hidden'
      }}>
        <LeftPanel 
          featureInput={featureInput}
          setFeatureInput={setFeatureInput}
          triggerAnalysis={triggerAnalysis}
          analysisState={analysisState}
        />
        
        <RightPanel 
          analysisState={analysisState}
          featureInput={featureInput}
          resultData={resultData}
          setAnalysisState={setAnalysisState}
          setResultData={setResultData}
        />
      </div>
    </div>
  );
}
