const chatBox = document.getElementById("chat-box");
const input = document.getElementById("user-input");

async function sendMessage() {
  console.log("📨 Sending message to backend...");

  const userMessage = input.value.trim();
  if (!userMessage) return;

  // Show user message
  appendMessage("You", userMessage, "user");
  input.value = "";

  // Show loading
  const loadingId = appendMessage("AI", "Typing...", "bot loading");

  try {
    const res = await fetch("http://localhost:8000/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: userMessage })
    });

    if (!res.ok) {
      throw new Error(`HTTP error ${res.status}`);
    }

    const data = await res.json();
    console.log("Backend response:", data);

    // Remove loading
    removeMessage(loadingId);

    const replyText = data.reply || "(No response from backend)";

    // Basic tool detection (UI-only hint)
    let toolUsed = "";
    if (/sunny|cloudy|rainy|weather|temperature/i.test(replyText)) {
      toolUsed = "Weather Tool";
    } else if (/definition|means|refers to|lasting/i.test(replyText)) {
      toolUsed = "Dictionary Tool";
    } else if (/search|result|found|according to/i.test(replyText)) {
      toolUsed = "Web Search Tool";
    }

    const finalText = toolUsed
      ? `${replyText}\n🛠 Tool used: ${toolUsed}`
      : replyText;

    appendMessage("AI", finalText, "bot");

  } catch (err) {
    console.error("Frontend error:", err);
    removeMessage(loadingId);
    appendMessage("AI", "Error connecting to backend.", "bot");
  }
}

// Append message safely
function appendMessage(sender, text, cls) {
  const msg = document.createElement("div");
  msg.className = `message ${cls}`;
  msg.innerText = `${sender}: ${text}`;

  const id = "msg-" + Math.random().toString(36).slice(2);
  msg.id = id;

  chatBox.appendChild(msg);
  chatBox.scrollTop = chatBox.scrollHeight;

  return id;
}

// Remove message by ID
function removeMessage(id) {
  const msg = document.getElementById(id);
  if (msg) msg.remove();
}
