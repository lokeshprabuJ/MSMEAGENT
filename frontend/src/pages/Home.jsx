import React, { useState } from 'react';

const Home = () => {
  const [input, setInput] = useState('');
  const [result, setResult] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();

    const res = await fetch('https://msmeagent.onrender.com/api/automation-suggest', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ problem: input }),
    });

    const data = await res.json();
    setResult(data);
  };

  return (
    <div className="p-4 max-w-2xl mx-auto">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <label className="text-lg font-medium">Describe your business problem:</label>
        <textarea
          className="p-3 border rounded-md"
          placeholder="e.g., I have 3 workers packing masala powder..."
          rows={5}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          required
        />
        <button type="submit" className="bg-green-600 text-white p-2 rounded-md hover:bg-green-700">
          Get Automation Suggestions
        </button>
      </form>

      {result && (
        <div className="mt-6 bg-gray-100 p-4 rounded-md shadow">
          <h2 className="text-xl font-bold mb-2">Results:</h2>
          <p><strong>Suggested Automation:</strong> {result.suggestion}</p>
          <p><strong>Estimated ROI:</strong> {result.roi_months ? result.roi_months + ' months' : 'N/A'}</p>
          <p><strong>Vendors:</strong> {result.vendors && result.vendors.length > 0 ? result.vendors.map(v => v.vendor_name || v.name).join(', ') : 'N/A'}</p>
        </div>
      )}
    </div>
  );
};

export default Home;
