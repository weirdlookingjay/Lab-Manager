const BACKEND_URL = "http://localhost:8000";

export async function GET() {
  try {
    console.log('Fetching logs from backend');
    const res = await fetch(`${BACKEND_URL}/logs`);
    
    if (!res.ok) {
      console.error('Failed to fetch logs from backend:', res.status, res.statusText);
      return new Response("Failed to fetch logs", { status: 500 });
    }

    const data = await res.json();
    return Response.json(data);
  } catch (error) {
    console.error('Error fetching logs:', error);
    return new Response("Error fetching logs", { status: 500 });
  }
}