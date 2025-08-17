import React, { useState } from "react";

const datasets = {
  objections: [
    { id: 1, objection: "I don’t want to pay $297/month", rebuttal: "If $297 got you 2 closings worth $10k+, would it be worth it?" },
    { id: 2, objection: "I’m already paying for leads", rebuttal: "Zillow is retail. Our system is wholesale. Would you rather rent or own?" }
  ],
  faqs: [
    { id: 1, question: "How many leads can I expect?", rebuttal: "75–100 a month on $300 budget, $3–$5/lead." },
    { id: 2, question: "Are leads exclusive?", rebuttal: "Yes, ads run in your account. Leads are 100% yours." }
  ]
};

export default function StringletApp() {
  const [selectedSet, setSelectedSet] = useState("objections");
  const [search, setSearch] = useState("");
  const [favorites, setFavorites] = useState([]);

  const currentData = datasets[selectedSet].filter(item =>
    (item.objection || item.question).toLowerCase().includes(search.toLowerCase())
  );

  const toggleFavorite = (id) => {
    setFavorites(prev =>
      prev.includes(id) ? prev.filter(f => f !== id) : [...prev, id]
    );
  };

  const copyText = (text) => {
    navigator.clipboard.writeText(text);
    alert("Copied to clipboard!");
  };

  const downloadText = (text, filename = "rebuttal.txt") => {
    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div style={{ fontFamily: "sans-serif", padding: 20 }}>
      <h2>Agent Rebuttal Library</h2>

      {/* Radio selector */}
      <div style={{ marginBottom: 20 }}>
        {Object.keys(datasets).map(key => (
          <label key={key} style={{ marginRight: 15 }}>
            <input
              type="radio"
              value={key}
              checked={selectedSet === key}
              onChange={() => setSelectedSet(key)}
            />
            {key.charAt(0).toUpperCase() + key.slice(1)}
          </label>
        ))}
      </div>

      {/* Search box */}
      <input
        type="text"
        placeholder="Search..."
        value={search}
        onChange={e => setSearch(e.target.value)}
        style={{ width: "100%", padding: 8, marginBottom: 20 }}
      />

      {/* List */}
      <div style={{ maxHeight: 400, overflowY: "auto", border: "1px solid #ddd", padding: 10 }}>
        {currentData.map(item => (
          <div key={item.id} style={{ marginBottom: 20 }}>
            <strong>{item.objection || item.question}</strong>
            <p>{item.rebuttal}</p>
            <button onClick={() => copyText(item.rebuttal)}>Copy</button>
            <button onClick={() => downloadText(item.rebuttal)}>Download</button>
            <button onClick={() => toggleFavorite(item.id)}>
              {favorites.includes(item.id) ? "★ Unfavorite" : "☆ Favorite"}
            </button>
          </div>
        ))}
      </div>

      {/* Favorites */}
      {favorites.length > 0 && (
        <div style={{ marginTop: 20 }}>
          <h3>Favorites</h3>
          {datasets[selectedSet]
            .filter(item => favorites.includes(item.id))
            .map(item => (
              <div key={item.id}>
                <strong>{item.objection || item.question}</strong>
                <p>{item.rebuttal}</p>
              </div>
            ))}
        </div>
      )}
    </div>
  );
}
