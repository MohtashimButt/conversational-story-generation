import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import StoryGenerator from "./storyGenerator";
import StoryDisplay from "./storyDisplay";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<StoryGenerator />} />
        <Route path="/story" element={<StoryDisplay />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
