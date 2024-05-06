// api.js

const API_URL = "http://localhost:5000";

export async function generateStory(data) {
  try {
    const response = await fetch(`${API_URL}/generate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      throw new Error("Network response was not ok.");
    }
    const storyData = await response.json();
    return storyData;
  } catch (error) {
    throw error;
  }
}
