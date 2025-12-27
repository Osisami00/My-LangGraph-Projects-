import { getAgentResponse } from "./api.js";

const chatWindow = document.getElementById("chat-window");
const chatForm = document.getElementById("chat-form");
const userInput = document.getElementById("user-input");

function addMessage(content, sender) {
  const msg = document.createElement("div");
  msg.className = `message ${sender}`;
  
  // Replace line breaks with <br> for HTML display
  msg.innerHTML = content.replace(/\n/g, "<br>");
  
  chatWindow.appendChild(msg);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}


function showTyping() {
  const typing = document.createElement("div");
  typing.className = "typing";
  typing.id = "typing";
  typing.textContent = "Agent is typing...";
  chatWindow.appendChild(typing);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function removeTyping() {
  const typing = document.getElementById("typing");
  if (typing) typing.remove();
}

chatForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const message = userInput.value.trim();
  if (!message) return;

  addMessage(message, "user");
  userInput.value = "";

  showTyping();
  const response = await getAgentResponse(message);
  removeTyping();
  addMessage(response, "agent");
});


