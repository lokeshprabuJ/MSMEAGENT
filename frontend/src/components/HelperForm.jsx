import React, { useState } from 'react';

const HelperForm = () => {
  const [input, setInput] = useState('');
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    setLoading(true);
    setResponse('');

    try {
      const res = await fetch('https://msmeagent.onrender.com/api/automation-suggest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ problem: input })
      });
      const data = await res.json();
      setResponse(data?.response || 'No response received.');
    } catch (err) {
      setResponse('Error connecting to backend.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white p-6 rounded-xl shadow-md space-y-4">
      <label htmlFor="input" className="block font-medium">Describe your factory or problem:</label>
      <textarea
        id="input"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="e.g., I have 3 people packing masala powder"
        rows="4"
        className="w-full p-3 border border-gray-300 rounded-lg"
      />
      <button
        type="submit"
        className="w-full bg-green-600 text-white py-2 rounded-lg hover:bg-green-700"
      >
        {loading ? 'Analyzing...' : 'Suggest Automation'}
      </button>

      {response && (
        <div className="mt-4 p-4 border border-green-400 rounded-lg bg-green-50">
          <strong>Automation Suggestion:</strong>
          <p className="mt-2 text-gray-700 whitespace-pre-line">{response}</p>
        </div>
      )}
    </form>
  );
};

export default HelperForm;
