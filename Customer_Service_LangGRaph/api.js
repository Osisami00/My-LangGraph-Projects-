export async function getAgentResponse(userMessage) {
  try {
    const response = await fetch("http://127.0.0.1:8000/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: userMessage,
        thread_id: "customer-001"
      })
    });

    if (!response.ok) {
      throw new Error(`Server error: ${response.status}`);
    }

    const data = await response.json();
    return data.reply;

  } catch (err) {
    console.error("API error:", err);
    return "Sorry, I'm having trouble connecting right now.";
  }
}
