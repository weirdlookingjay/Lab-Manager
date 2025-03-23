from pathlib import Path
import json
import base64
from typing import Dict, Any, List
from datetime import datetime

from django.http import JsonResponse, HttpRequest
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required

from .utils import get_computer_or_404
from .utils.logging import log_file_event
from .models import Computer
from .websocket_client import RelayClient

def format_file_info(path: Path) -> Dict[str, Any]:
    """Format file information into a consistent structure."""
    stat = path.stat()
    return {
        'name': path.name,
        'path': str(path),
        'isDirectory': path.is_dir(),
        'size': stat.st_size if path.is_file() else None,
        'modifiedTime': datetime.fromtimestamp(stat.st_mtime).isoformat()
    }

def list_directory(path: Path) -> List[Dict[str, Any]]:
    """List contents of a directory with file information."""
    try:
        files = []
        for item in path.iterdir():
            try:
                files.append(format_file_info(item))
            except (PermissionError, OSError):
                # Skip files we can't access
                continue
        return sorted(files, key=lambda x: (not x['isDirectory'], x['name'].lower()))
    except PermissionError:
        return []

@login_required
@require_http_methods(['GET'])
def list_local_files(request: HttpRequest) -> JsonResponse:
    """List files in the local file system."""
    path = request.GET.get('path', '/')
    try:
        target_path = Path(path).resolve()
        if not target_path.exists():
            return JsonResponse({'error': 'Path does not exist'}, status=404)
        
        files = list_directory(target_path)
        return JsonResponse({'files': files}, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
@require_http_methods(['GET'])
def list_remote_files(request: HttpRequest, computer_id: int) -> JsonResponse:
    """List files on a remote computer."""
    computer = get_computer_or_404(computer_id)
    path = request.GET.get('path', '/')
    
    try:
        # Send list_files command to computer agent
        client = RelayClient()
        response = client.send_command(computer.agent_id, {
            'command': 'list_files',
            'path': path
        })
        
        if response.get('error'):
            return JsonResponse({'error': response['error']}, status=400)
        
        # Log successful file listing
        log_file_event(
            event='list_files',
            file_path=path,
            computer=computer,
            user=request.user,
            details={'file_count': len(response.get('files', []))}
        )
        
        return JsonResponse({'files': response.get('files', [])}, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(['POST'])
def download_file(request: HttpRequest, computer_id: int) -> JsonResponse:
    """Download a file from a remote computer."""
    computer = get_computer_or_404(computer_id)
    
    try:
        data = json.loads(request.body)
        remote_path = data.get('remotePath')
        local_path = data.get('localPath')
        
        if not remote_path or not local_path:
            return JsonResponse({'error': 'Both remotePath and localPath are required'}, status=400)
        
        # Send download command to computer agent
        client = RelayClient()
        response = client.send_command(computer.agent_id, {
            'command': 'download_file',
            'remote_path': remote_path,
            'local_path': local_path
        })
        
        if response.get('error'):
            return JsonResponse({'error': response['error']}, status=400)
        
        # Decode base64 content and write to local path
        content = base64.b64decode(response['content'])
        local_path = Path(local_path)
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_bytes(content)
        
        # Log successful download
        log_file_event(
            event='download_file',
            file_path=remote_path,
            computer=computer,
            user=request.user,
            details={'local_path': str(local_path), 'size': len(content)}
        )
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(['POST'])
def upload_file(request: HttpRequest, computer_id: int) -> JsonResponse:
    """Upload a file to a remote computer."""
    computer = get_computer_or_404(computer_id)
    
    try:
        data = json.loads(request.body)
        local_path = data.get('localPath')
        remote_path = data.get('remotePath')
        
        if not local_path or not remote_path:
            return JsonResponse({'error': 'Both localPath and remotePath are required'}, status=400)
        
        # Read and encode local file
        local_path = Path(local_path)
        if not local_path.exists():
            return JsonResponse({'error': 'Local file does not exist'}, status=404)
        
        content = local_path.read_bytes()
        content_b64 = base64.b64encode(content).decode('utf-8')
        
        # Send upload command to computer agent
        client = RelayClient()
        response = client.send_command(computer.agent_id, {
            'command': 'upload_file',
            'local_path': local_path,
            'remote_path': remote_path,
            'file_content': content_b64
        })
        
        if response.get('error'):
            return JsonResponse({'error': response['error']}, status=400)
        
        # Log successful upload
        log_file_event(
            event='upload_file',
            file_path=remote_path,
            computer=computer,
            user=request.user,
            details={'local_path': str(local_path), 'size': len(content)}
        )
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
