const BACKEND_URL = "http://localhost:8000";

export async function POST(request: Request) {
  try {
    console.log('Scheduling new job...');
    const body = await request.json();
    console.log('Schedule request body:', body);
    
    // Get local timezone offset in minutes
    const date = new Date();
    const timezoneOffsetMinutes = date.getTimezoneOffset();
    const timezoneName = Intl.DateTimeFormat().resolvedOptions().timeZone;
    
    // Create a date object for the scheduled time today
    const scheduleDate = new Date();
    scheduleDate.setHours(body.hour, body.minute, 0, 0);
    
    console.log('Timezone information:', {
      timezoneName,
      offsetMinutes: timezoneOffsetMinutes,
      offsetHours: timezoneOffsetMinutes / 60
    });
    
    // Adjust hour and minute for local timezone
    let localHour = body.hour;
    let localMinute = body.minute;
    
    // Convert to UTC for the server (ADD the offset since getTimezoneOffset returns a negative value for EST)
    let totalMinutes = (localHour * 60 + localMinute) + timezoneOffsetMinutes;
    let utcHour = Math.floor(totalMinutes / 60) % 24;
    let utcMinute = totalMinutes % 60;
    
    // Handle day wraparound
    if (utcHour < 0) utcHour += 24;
    if (utcMinute < 0) utcMinute += 60;
    
    console.log('Schedule details:', {
      requestedTime: `${localHour.toString().padStart(2, '0')}:${localMinute.toString().padStart(2, '0')} ${timezoneName}`,
      localTime: scheduleDate.toLocaleTimeString(),
      utcTime: `${utcHour.toString().padStart(2, '0')}:${utcMinute.toString().padStart(2, '0')} UTC`
    });
    
    // Construct URL with query parameters using UTC time
    const url = new URL(`${BACKEND_URL}/schedule`);
    url.searchParams.set('hour', localHour.toString());  // Use local time instead of UTC
    url.searchParams.set('minute', localMinute.toString());  // Use local time instead of UTC
    if (body.name) {
      url.searchParams.set('name', body.name);
    }
    
    console.log('Sending request to:', url.toString());

    const requestOptions = {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
      }
    };
    console.log('Request options:', requestOptions);

    const res = await fetch(url.toString(), requestOptions);
    console.log('Response status:', res.status, res.statusText);
    
    const responseText = await res.text();
    console.log('Raw response:', responseText);

    if (!res.ok) {
      console.error('Failed to schedule job:', {
        status: res.status,
        statusText: res.statusText,
        response: responseText
      });
      return Response.json({ 
        error: "Failed to schedule job",
        details: responseText
      }, { 
        status: res.status 
      });
    }

    try {
      const data = JSON.parse(responseText);
      console.log('Job scheduled successfully:', data);
      return Response.json({
        ...data,
        scheduleDetails: {
          requestedTime: `${localHour.toString().padStart(2, '0')}:${localMinute.toString().padStart(2, '0')} ${timezoneName}`,
          utcTime: `${utcHour.toString().padStart(2, '0')}:${utcMinute.toString().padStart(2, '0')} UTC`
        }
      });
    } catch (parseError) {
      console.error('Error parsing response:', parseError);
      return Response.json({ 
        error: "Invalid response format",
        details: responseText
      }, { 
        status: 500 
      });
    }
  } catch (error) {
    console.error('Error in schedule endpoint:', error);
    return Response.json({ 
      error: "Error scheduling job",
      details: error instanceof Error ? error.message : String(error)
    }, { 
      status: 500 
    });
  }
} 