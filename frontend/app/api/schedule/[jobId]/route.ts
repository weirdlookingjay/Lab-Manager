const BACKEND_URL = "http://localhost:8000";

export async function DELETE(
  request: Request,
  { params }: { params: { jobId: string } }
) {
  try {
    console.log('Deleting schedule:', params.jobId);
    const res = await fetch(`${BACKEND_URL}/schedule/${params.jobId}`, {
      method: 'DELETE',
      headers: {
        'Accept': 'application/json'
      }
    });
    
    const responseText = await res.text();
    console.log('Delete response:', {
      status: res.status,
      statusText: res.statusText,
      response: responseText
    });
    
    if (!res.ok) {
      console.error('Failed to delete schedule:', {
        status: res.status,
        statusText: res.statusText,
        response: responseText
      });
      return Response.json({ 
        error: "Failed to delete schedule",
        details: responseText
      }, { 
        status: res.status 
      });
    }

    try {
      const data = JSON.parse(responseText);
      console.log('Schedule deleted successfully:', data);
      return Response.json(data);
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
    console.error('Error deleting schedule:', error);
    return Response.json({ 
      error: "Error deleting schedule",
      details: error instanceof Error ? error.message : String(error)
    }, { 
      status: 500 
    });
  }
} 