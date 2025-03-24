const BACKEND_URL = "http://localhost:8000";

export async function GET() {
  try {
    console.log('Fetching schedules from backend:', `${BACKEND_URL}/schedules`);
    
    const res = await fetch(`${BACKEND_URL}/schedules`, {
      headers: {
        'Accept': 'application/json',
      },
      cache: 'no-store' // Disable caching
    });
    
    if (!res.ok) {
      const errorText = await res.text();
      console.error('Failed to fetch schedules from backend:', {
        status: res.status,
        statusText: res.statusText,
        error: errorText
      });
      return Response.json({ 
        error: "Failed to fetch schedules",
        details: errorText
      }, { 
        status: res.status 
      });
    }

    const data = await res.json();
    console.log('Successfully fetched schedules:', data);
    
    // Ensure we have the expected data structure
    if (!data.schedules) {
      console.error('Unexpected response format:', data);
      return Response.json({
        schedules: []
      });
    }

    return Response.json(data);
  } catch (error) {
    console.error('Error in schedules endpoint:', error);
    return Response.json({ 
      error: "Error fetching schedules",
      details: error instanceof Error ? error.message : String(error)
    }, { 
      status: 500 
    });
  }
} 