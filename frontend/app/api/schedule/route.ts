// app/api/schedule/route.ts

const BACKEND_URL = "http://localhost:8000"; // Your FastAPI backend URL

// Handle POST requests
export const POST = async (req: Request) => {
  const url = new URL(req.url);
  const pathname = url.pathname.replace("/api/schedule", "");
  
  console.log('Received request URL:', url.toString());
  console.log('Pathname after processing:', pathname);
  
  try {
    const scheduleData = await req.json();
    console.log('Received schedule data:', scheduleData);
    
    const res = await fetch(`${BACKEND_URL}/api/scans/schedule/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(scheduleData),
    });

    if (!res.ok) {
      const errorText = await res.text();
      console.error('Error from backend:', errorText);
      return new Response(errorText, { status: res.status });
    }

    const data = await res.json();
    return new Response(JSON.stringify(data), {
      headers: { "Content-Type": "application/json" },
    });
  } catch (error) {
    console.error('Error processing schedule request:', error);
    return new Response(JSON.stringify({ error: 'Failed to process schedule request' }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
};

// Handle GET requests
export const GET = async (req: Request) => {
  try {
    const res = await fetch(`${BACKEND_URL}/api/scans/schedule/`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!res.ok) {
      const errorText = await res.text();
      console.error('Error fetching schedule:', errorText);
      return new Response(errorText, { status: res.status });
    }

    const data = await res.json();
    return new Response(JSON.stringify(data), {
      headers: { "Content-Type": "application/json" },
    });
  } catch (error) {
    console.error('Error fetching schedule:', error);
    return new Response(JSON.stringify({ error: 'Failed to fetch schedule' }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
};
