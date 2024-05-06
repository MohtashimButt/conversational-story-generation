import React from "react";
import { useLocation, useNavigate } from "react-router-dom";

function StoryDisplay() {
  const location = useLocation();
  const navigate = useNavigate();
  const { data } = location.state;
  console.log(data);

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col items-center justify-center">
      <div className="bg-white p-8 rounded-lg shadow-lg max-w-4xl w-full space-y-6">
        <h1 className="text-2xl font-bold text-center">
          Generated Story and Image
        </h1>
        {data.map((item) => (
          <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0 md:space-x-4">
            <div className="md:w-1/2">
              <h2 className="text-lg font-semibold">Story</h2>
              <p className="text-gray-700">{item.story}</p>
            </div>
            <div className="md:w-1/2">
              <img
                src={item.image}
                alt="Generated"
                className="max-w-full h-auto rounded-lg shadow-lg"
              />
            </div>
          </div>
        ))}
        <button
          onClick={() => navigate("/")}
          className="mt-4 py-2 px-4 bg-blue-500 text-white rounded hover:bg-blue-600 focus:outline-none focus:bg-blue-700"
        >
          Generate New Story
        </button>
      </div>
    </div>
  );
}

export default StoryDisplay;
