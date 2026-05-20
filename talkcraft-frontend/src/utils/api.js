const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function startMic() {
  const res = await fetch(`${API_URL}/start-mic`, { method: "POST" });
  return res.json();
}

export async function uploadFile(file) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_URL}/start-file`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Upload failed");
  }
  return res.json();
}

export async function stopEngine() {
  const res = await fetch(`${API_URL}/stop`, { method: "POST" });
  return res.json();
}

export async function getState() {
  const res = await fetch(`${API_URL}/state`);
  return res.json();
}
