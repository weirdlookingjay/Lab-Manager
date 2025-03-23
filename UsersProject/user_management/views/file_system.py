import os
import json
from datetime import datetime
import asyncio
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from asgiref.sync import async_to_sync
from ..models import Computer
from ..websocket_client import relay_client

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_local_files(request):
    """List files in the local file system"""
    path = request.GET.get('path', '/')
    
    try:
        # List directory contents
        entries = []
        with os.scandir(path) as it:
            for entry in it:
                try:
                    stat = entry.stat()
                    entries.append({
                        'name': entry.name,
                        'path': os.path.join(path, entry.name),
                        'isDirectory': entry.is_dir(),
                        'size': stat.st_size if not entry.is_dir() else None,
                        'modifiedTime': datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
                except (PermissionError, OSError):
                    continue
                    
        # Sort directories first, then files
        entries.sort(key=lambda x: (not x['isDirectory'], x['name'].lower()))
        return JsonResponse(entries, safe=False)
        
    except (FileNotFoundError, PermissionError) as e:
        return JsonResponse({'error': str(e)}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_remote_files(request, computer_id):
    """List files on the remote computer"""
    path = request.GET.get('path', '/')
    
    try:
        computer = Computer.objects.get(id=computer_id)
        if not computer.is_online:
            return JsonResponse({'error': 'Computer is offline'}, status=400)
            
        # Send list_files command to agent
        command = {
            'type': 'command',
            'command': 'list_files',
            'path': path,
            'hostname': computer.hostname
        }
        
        # Send command through relay client
        response = async_to_sync(relay_client.send_command)(command)
        if response.get('error'):
            return JsonResponse({'error': response['error']}, status=400)
            
        files = response.get('files', [])
        return JsonResponse(files, safe=False)
        
    except Computer.DoesNotExist:
        return JsonResponse({'error': 'Computer not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def download_file(request, computer_id):
    """Download a file from the remote computer"""
    try:
        data = json.loads(request.body)
        remote_path = data.get('remotePath')
        local_path = data.get('localPath')
        
        if not remote_path or not local_path:
            return JsonResponse({'error': 'Missing required parameters'}, status=400)
            
        computer = Computer.objects.get(id=computer_id)
        if not computer.is_online:
            return JsonResponse({'error': 'Computer is offline'}, status=400)
            
        # Send download command to agent
        command = {
            'type': 'command',
            'command': 'download_file',
            'remote_path': remote_path,
            'local_path': local_path,
            'hostname': computer.hostname
        }
        
        # Send command through relay client
        response = async_to_sync(relay_client.send_command)(command)
        if response.get('error'):
            return JsonResponse({'error': response['error']}, status=400)
            
        return JsonResponse({'status': 'success'})
        
    except Computer.DoesNotExist:
        return JsonResponse({'error': 'Computer not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_file(request, computer_id):
    """Upload a file to the remote computer"""
    try:
        data = json.loads(request.body)
        local_path = data.get('localPath')
        remote_path = data.get('remotePath')
        
        if not local_path or not remote_path:
            return JsonResponse({'error': 'Missing required parameters'}, status=400)
            
        computer = Computer.objects.get(id=computer_id)
        if not computer.is_online:
            return JsonResponse({'error': 'Computer is offline'}, status=400)
            
        # Send upload command to agent
        command = {
            'type': 'command',
            'command': 'upload_file',
            'local_path': local_path,
            'remote_path': remote_path,
            'hostname': computer.hostname
        }
        
        # Send command through relay client
        response = async_to_sync(relay_client.send_command)(command)
        if response.get('error'):
            return JsonResponse({'error': response['error']}, status=400)
            
        return JsonResponse({'status': 'success'})
        
    except Computer.DoesNotExist:
        return JsonResponse({'error': 'Computer not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
