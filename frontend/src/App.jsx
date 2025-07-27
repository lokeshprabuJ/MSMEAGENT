import { useState, useRef } from 'react';
import './App.css';
import Header from './components/Header';

function App() {
  const [input, setInput] = useState({
    businessType: '',
    numWorkers: '',
    automationGoal: '',
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [transcribing, setTranscribing] = useState(false);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  const handleChange = (e) => {
    setInput({ ...input, [e.target.name]: e.target.value });
  };

  const handleSubmit = async () => {
    setError('');
    setResult(null);
    const query = `I run a ${input.businessType} unit with ${input.numWorkers} workers. ${input.automationGoal}`;
    try {
      setLoading(true);
      const backendUrl = import.meta.env.VITE_API_URL || 'https://msmeagent.onrender.com';
      console.log('Sending request to:', `${backendUrl}/api/automation-suggest`);
      console.log('Request body:', { problem: query });
      
      const response = await fetch(`${backendUrl}/api/automation-suggest`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ problem: query })
      });
      
      console.log('Response status:', response.status);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Server error:', errorText);
        throw new Error(`Server error: ${response.status} - ${errorText}`);
      }
      
      const data = await response.json();
      console.log('Response data:', data);
      setResult(data);
    } catch (error) {
      console.error('Full error:', error);
      setError(`Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleVoiceInput = async () => {
    setError('');
    setTranscribing(true);
    setInput((prev) => ({ ...prev, automationGoal: '' }));
    try {
      if (!navigator.mediaDevices || !window.MediaRecorder) {
        setError('Voice input not supported in this browser.');
        setTranscribing(false);
        return;
      }
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new window.MediaRecorder(stream);
      audioChunksRef.current = [];
      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };
      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        const formData = new FormData();
        formData.append('file', audioBlob, 'voice.wav');
        try {
          const backendUrl = import.meta.env.VITE_API_URL || 'https://msmeagent.onrender.com';
          const res = await fetch(`${backendUrl}/api/transcribe`, {
            method: 'POST',
            body: formData
          });
          if (!res.ok) throw new Error('Transcription failed');
          const data = await res.json();
          setInput((prev) => ({ ...prev, automationGoal: data.text }));
        } catch (err) {
          setError('Transcription failed.');
        } finally {
          setTranscribing(false);
        }
      };
      mediaRecorder.start();
      setTimeout(() => {
        mediaRecorder.stop();
        stream.getTracks().forEach((track) => track.stop());
      }, 5000); // Record for 5 seconds
    } catch (err) {
      setError('Could not access microphone.');
      setTranscribing(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <div className="app max-w-xl mx-auto mt-8 bg-white p-8 rounded-xl shadow-md">
        <h1 className="text-2xl font-bold mb-6 text-center">🤖 MSME Automation Helper</h1>
        <label className="block mb-4">
          🏭 Business Type:
          <input
            type="text"
            name="businessType"
            placeholder="e.g. masala packing"
            value={input.businessType}
            onChange={handleChange}
            className="w-full p-2 border border-gray-300 rounded mt-1"
          />
        </label>
        <label className="block mb-4">
          👷‍♂️ Number of Workers:
          <input
            type="number"
            name="numWorkers"
            placeholder="e.g. 5"
            value={input.numWorkers}
            onChange={handleChange}
            className="w-full p-2 border border-gray-300 rounded mt-1"
          />
        </label>
        <label className="block mb-4">
          🎯 Automation Goal:
          <textarea
            name="automationGoal"
            placeholder="Describe what automation help you need..."
            value={input.automationGoal}
            onChange={handleChange}
            rows="4"
            className="w-full p-2 border border-gray-300 rounded mt-1"
          />
          <button
            type="button"
            onClick={handleVoiceInput}
            disabled={transcribing}
            className="mt-2 bg-blue-600 text-white px-4 py-1 rounded hover:bg-blue-700"
          >
            {transcribing ? 'Listening...' : '🎤 Speak'}
          </button>
        </label>
        <button
          onClick={handleSubmit}
          disabled={loading}
          className="w-full bg-green-600 text-white py-2 rounded-lg hover:bg-green-700 mb-4"
        >
          {loading ? 'Processing...' : 'Get Automation Help'}
        </button>
        {error && (
          <div className="mb-4 p-3 bg-red-100 text-red-700 rounded">{error}</div>
        )}
        {result && (
          <div className="mt-4 p-4 border border-green-400 rounded-lg bg-green-50">
            <h2 className="text-lg font-bold mb-2">Automation Suggestion</h2>
            <p><strong>Machine:</strong> {result.machine_name || 'N/A'}</p>
            <p><strong>Estimated Cost:</strong> ₹{result.machine_cost || 'N/A'}</p>
            <p><strong>ROI:</strong> {result.roi_months ? result.roi_months + ' months' : 'N/A'}</p>
            <p><strong>Manpower Savings:</strong> {result.manpower_savings || 'N/A'}</p>
            <p><strong>Vendors:</strong> {result.vendors && result.vendors.length > 0 ? result.vendors.map(v => `${v.vendor_name} (${v.location})`).join(', ') : 'N/A'}</p>
            <div className="mt-2 text-gray-700 whitespace-pre-line">
              {result.suggestion}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
