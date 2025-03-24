const BACKEND_URL = "http://localhost:8000";

export async function POST() {
  console.log('Handling POST request in /run route');
  const res = await fetch(`${BACKEND_URL}/run`, { 
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    }
  });

  if (!res.ok) {
    console.error('Backend request failed:', res.status, res.statusText);
    return new Response("Failed to run the task", { status: 500 });
  }

  const data = await res.json();
  return Response.json(data);
} 