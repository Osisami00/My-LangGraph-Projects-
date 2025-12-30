const chatBox = document.getElementById("chat-box");
const input = document.getElementById("user-input");

async function sendMessage() {
  const userMessage = input.value.trim();
  if (!userMessage) return;

  // Display user message
  appendMessage("You", userMessage, "user");
  input.value = "";

  // Display loading state
  const loadingId = appendMessage("AI", "Typing...", "bot loading");

  try {
    const res = await fetch("http://localhost:8000/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: userMessage })
    });

    const data = await res.json();
    // Remove loading text
    removeMessage(loadingId);

    // Extract reply
    const replyText = data.reply;

    // Detect tool usage (basic simulation)
    let toolUsed = "";
    if (/Weather|temperature|Sunny|Cloudy|Rainy/i.test(replyText)) toolUsed = "Weather Tool";
    else if (/Definition|lasting|ephemeral|agent/i.test(replyText)) toolUsed = "Dictionary Tool";
    else if (/search|https?:\/\/|No results/i.test(replyText)) toolUsed = "Web Search Tool";

    appendMessage("AI", replyText + (toolUsed ? `\n🛠 Used: ${toolUsed}` : ""), "bot");

  } catch (err) {
    removeMessage(loadingId);
    appendMessage("AI", "⚠️ Error: Could not get response.", "bot");
    console.error(err);
  }
}

// Helper to append messages
function appendMessage(sender, text, cls) {
  const msg = document.createElement("div");
  msg.classList.add("message", cls);
  msg.innerText = `${sender}: ${text}`;
  chatBox.appendChild(msg);
  chatBox.scrollTop = chatBox.scrollHeight;

  // Return element ID for removal
  const id = Date.now();
  msg.id = id;
  return id;
}

// Remove a message (used for loading)
function removeMessage(id) {
  const msg = document.getElementById(id);
  if (msg) msg.remove();
}
