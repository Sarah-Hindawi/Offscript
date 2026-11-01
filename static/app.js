async function checkHealth() {
  const el = document.getElementById("health");
  try {
    const res = await fetch("/api/health");
    const data = await res.json();
    const env = data.env;
    el.textContent =
      `Server ${data.status} · ElevenLabs key: ${env.elevenlabs_key ? "set" : "missing"}` +
      ` · LLM key: ${env.llm_key ? "set" : "missing"} · model: ${env.llm_model || "unset"}`;
  } catch (err) {
    el.textContent = "Server unreachable";
  }
}

checkHealth();
