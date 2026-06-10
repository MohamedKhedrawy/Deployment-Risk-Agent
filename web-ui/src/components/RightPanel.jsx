import React from 'react';
import IdleState from './states/IdleState';
import LoadingState from './states/LoadingState';
import ResultState from './states/ResultState';

export default function RightPanel({ analysisState, featureInput, resultData, setAnalysisState, setResultData }) {
  return (
    <div style={{
      flex: 1,
      padding: '20px',
      overflowY: 'auto',
      background: 'var(--bg-base)'
    }}>
      {analysisState === 'idle' && <IdleState />}
      {analysisState === 'loading' && <LoadingState feature={featureInput} setAnalysisState={setAnalysisState} setResultData={setResultData} />}
      {analysisState === 'result' && <ResultState data={resultData} />}
    </div>
  );
}
