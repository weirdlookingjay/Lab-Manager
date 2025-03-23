import datetime
import json
import os
import logging
import asyncio
import websockets
import time
import winrm
from typing import Dict, Any
from django.conf import settings
from pathlib import Path
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q
from django.shortcuts import get_object_or_404

from .authentication import CookieTokenAuthentication
from .models import (
    Computer, AuditLog, SystemLog, Command
)

from asgiref.sync import async_to_sync, sync_to_async
from .serializers import ComputerSerializer
from .websocket_client import relay_client

logger = logging.getLogger(__name__)

class ComputerViewSet(viewsets.ModelViewSet):
    """ViewSet for managing computers"""
    queryset = Computer.objects.all()
    serializer_class = ComputerSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieTokenAuthentication, TokenAuthentication, SessionAuthentication]

    def get_queryset(self):
        """Get filtered queryset based on request parameters."""
        queryset = Computer.objects.all()
        
        # Print all computer data for debugging
        print("\n=== Computer Data Debug Info ===")
        for computer in queryset:
            print(f"\nComputer: {computer.hostname}")
            print(f"Label: {computer.label}")
            print(f"IP Address: {computer.ip_address}")
            print(f"Last Seen: {computer.last_seen}")
            print(f"Last Metrics Update: {computer.last_metrics_update}")
            if computer.metrics:
                print(f"Metrics Data:")
                print(json.dumps(computer.metrics, indent=2))
            else:
                print("No metrics data available")
            print("-" * 50)
        
        # Filter by online status if requested
        online = self.request.query_params.get('online', None)
        if online is not None:
            thirty_mins_ago = timezone.now() - timezone.timedelta(minutes=30)
            if online.lower() == 'true':
                queryset = queryset.filter(
                    Q(last_metrics_update__gte=thirty_mins_ago) |
                    Q(last_seen__gte=thirty_mins_ago)
                )
            else:
                queryset = queryset.filter(
                    Q(last_metrics_update__lt=thirty_mins_ago) |
                    Q(last_metrics_update__isnull=True),
                    Q(last_seen__lt=thirty_mins_ago) |
                    Q(last_seen__isnull=True)
                )
            
        # Filter by search term
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(label__icontains=search) |
                Q(ip_address__icontains=search) |
                Q(model__icontains=search)
            )
            
        return queryset.order_by('label')
    
    def _calculate_disk_percent(self, total: int, used: int) -> float:
        """Calculate disk usage percentage."""
        if not total or not used:
            return 0.0
        return (used / total) * 100

    def get_computer_metrics(self, computer: Computer) -> Dict[str, Any]:
        """Get computer metrics in a standardized format."""
        metrics = computer.metrics or {}
        cpu_info = metrics.get('cpu', {})
        memory_info = metrics.get('memory', {})
        disk_info = metrics.get('disk', {})
        system_info = metrics.get('system', {})
        
        # Update computer fields from metrics
        computer.cpu_model = cpu_info.get('model')
        computer.cpu_cores = cpu_info.get('cores')
        computer.cpu_threads = cpu_info.get('threads')
        computer.memory_total = memory_info.get('total_bytes')
        computer.memory_usage = memory_info.get('percent')
        computer.total_disk = disk_info.get('total_bytes')
        computer.disk_usage = disk_info.get('percent')
        computer.device_class = system_info.get('device_class')
        computer.os_version = system_info.get('os_version')
        computer.logged_in_user = system_info.get('logged_in_user')
        computer.save()
        
        return {
            'status': 'online' if computer.get_status() == 'online' else 'offline',
            'cpu': cpu_info,
            'memory': memory_info,
            'disk': disk_info,
            'system': system_info,
            'last_seen': computer.last_seen.isoformat() if computer.last_seen else None,
            'last_metrics_update': computer.last_metrics_update.isoformat() if computer.last_metrics_update else None
        }

    def list(self, request):
        """List all computers with their current status."""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """Handle GET requests for a single computer."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def create(self, request):
        """Add a new computer."""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        """Remove a computer."""
        try:
            computer = self.get_queryset().get(pk=pk)
            computer.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Computer.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def perform_create(self, serializer):
        """Additional actions when creating a computer."""
        computer = serializer.save()
        # Log the creation
        AuditLog.objects.create(
            message=f'Computer {computer.label} ({computer.ip_address}) added to system',
            level='info'
        )

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update computer status and system metrics."""
        try:
            computer = self.get_object()
            data = request.data
            print(f"Received data for update: {data}")

            # Update computer info
            computer.is_online = True
            computer.last_seen = timezone.now()
            computer.model = data.get('model', computer.model)
            computer.os_version = data.get('os_version', computer.os_version)
            computer.ip_address = data.get('ip_address', computer.ip_address)
            computer.logged_in_user = data.get('logged_in_user')  # Update logged in user
            
            # Update system metrics
            computer.cpu_model = data.get('cpu_info', {}).get('model', computer.cpu_model)
            computer.cpu_speed = data.get('cpu_info', {}).get('speed', computer.cpu_speed)
            computer.cpu_cores = data.get('cpu_info', {}).get('cores', computer.cpu_cores)
            computer.cpu_threads = data.get('cpu_info', {}).get('threads', computer.cpu_threads)
            computer.cpu_architecture = data.get('cpu_info', {}).get('architecture', computer.cpu_architecture)
            
            computer.memory_total = data.get('memory_info', {}).get('total', computer.memory_total)
            computer.memory_available = data.get('memory_info', {}).get('available', computer.memory_available)
            computer.memory_used = data.get('memory_info', {}).get('used', computer.memory_used)
            
            computer.disk_total = data.get('disk_info', {}).get('total', computer.disk_total)
            computer.disk_free = data.get('disk_info', {}).get('free', computer.disk_free)
            computer.disk_used = data.get('disk_info', {}).get('used', computer.disk_used)
            
            computer.device_class = data.get('system_info', {}).get('device_class', computer.device_class)
            computer.boot_time = data.get('system_info', {}).get('boot_time', computer.boot_time)
            computer.system_uptime = data.get('system_info', {}).get('uptime', computer.system_uptime)
            
            computer.last_metrics_update = timezone.now()
            computer.save()

            # Log system metrics
            SystemLog.objects.create(
                computer=computer,
                category='COMPUTER_STATUS',
                event='COMPUTER_ONLINE',
                level='INFO',
                message=f"Computer {computer.label} reported status",
                details={
                    'cpu': {
                        'model': computer.cpu_model,
                        'speed': computer.cpu_speed,
                        'cores': computer.cpu_cores,
                        'threads': computer.cpu_threads,
                        'architecture': computer.cpu_architecture
                    },
                    'memory': {
                        'total': computer.memory_total,
                        'available': computer.memory_available,
                        'used': computer.memory_used,
                        'total_gb': f"{computer.memory_total / (1024 * 1024 * 1024):.1f}" if computer.memory_total else "0.0"
                    },
                    'disk': {
                        'total': computer.disk_total,
                        'free': computer.disk_free,
                        'used': computer.disk_used,
                        'total_gb': f"{computer.disk_total / (1024 * 1024 * 1024):.1f}" if computer.disk_total else "0.0",
                        'percent': self._calculate_disk_percent(computer.disk_total, computer.disk_used)
                    },
                    'system': {
                        'device_class': computer.device_class,
                        'uptime': computer.format_uptime(),
                        'boot_time': computer.boot_time.isoformat() if computer.boot_time else None,
                        'os_version': computer.os_version,
                        'logged_in_user': computer.logged_in_user
                    }
                }
            )

            return Response(self.get_serializer(computer).data)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def handle_websocket_message(self, message):
        """Handle messages from the WebSocket relay"""
        try:
            # Only process metrics messages for PC7
            if message.get('type') == 'metrics' and message.get('hostname') == 'PC7':
                print("\n" + "="*80)
                print("RAW PC7 MESSAGE:")
                print(json.dumps(message, indent=2))
                print("="*80 + "\n")
                
                # Stop here - just show raw message
                return
                
        except Exception as e:
            print(f"Error processing message: {e}")

    @action(detail=True, methods=['post'])
    def scan_directory(self, request, pk=None):
        """Scan a specific directory on the computer."""
        computer = self.get_object()
        directory = request.data.get('directory', '')
        try:
            print(f"Starting directory scan for {computer.name} at path: {directory}")
            
            # Get the destination directory
            dest_dir = os.path.join(settings.MEDIA_ROOT, 'pdfs', computer.name)
            os.makedirs(dest_dir, exist_ok=True)
            
            # Scan network directory
            files = scan_network_directory(computer.ip_address, share_path=directory)
            
            if not files:
                print(f"No PDF files found on {computer.name}")
                success = True  # Consider this a successful scan, just with no files
                return success
                
            # Validate files and collect processable ones
            valid_files = []
            for file_path in files:
                try:
                    # Check if file is accessible
                    if not check_file_access(file_path):
                        print(f"Skipping inaccessible file: {file_path}")
                        continue
                    
                    # Process O*NET PDF to get new filename
                    success, new_filename = process_onet_pdf(file_path)
                    if not success:
                        print(f"Error processing O*NET PDF {file_path}: {new_filename}")
                        continue
                        
                    valid_files.append((file_path, new_filename))
                    
                except Exception as file_error:
                    print(f"Error validating file {file_path}: {str(file_error)}")
                    continue
            
            # Only create destination directory if we have valid files to process
            if valid_files:
                dest_dir = os.path.join(settings.MEDIA_ROOT, 'pdfs', computer.name)
                os.makedirs(dest_dir, exist_ok=True)
                print(f"Created destination directory: {dest_dir}")
                
                # Process valid files
                processed_count = 0
                for file_path, new_filename in valid_files:
                    try:
                        # Check for duplicates before copying
                        if is_duplicate_onet(dest_dir, new_filename):
                            print(f"Skipping duplicate O*NET file: {new_filename}")
                            continue
                            
                        # Create destination path with new filename
                        dest_path = os.path.join(dest_dir, new_filename)
                        
                        # Copy file to destination with new name
                        shutil.copy2(file_path, dest_path)
                        print(f"Copied and renamed file: {os.path.basename(file_path)} -> {new_filename}")
                        processed_count += 1
                        
                    except Exception as copy_error:
                        print(f"Error copying file {file_path}: {str(copy_error)}")
                        continue
                
                print(f"Successfully processed {processed_count} files from {computer.name}")
            else:
                print(f"No valid files to process from {computer.name}")
            
            success = True
            
        except Exception as e:
            print(f"Error scanning {computer.name}: {str(e)}")
            success = False
            
        finally:
            try:
                # Always try to disconnect and log the result
                self._disconnect_computer(computer)
                print(f"Successfully disconnected from {computer.name}")
            except Exception as disconnect_error:
                print(f"Error disconnecting from {computer.name}: {str(disconnect_error)}")
                
        return success

    @action(detail=False, methods=['post'])
    def report(self, request):
        hostname = request.data.get('hostname')
        if not hostname:
            return Response({'error': 'Hostname is required'}, status=status.HTTP_400_BAD_REQUEST)

        computer, created = Computer.objects.get_or_create(
            hostname=hostname,
            defaults={'user': request.user}
        )

        # Update computer information
        computer.manufacturer = request.data.get('manufacturer', '')
        computer.model = request.data.get('model', '')
        computer.processor = request.data.get('processor', '')
        computer.ram = request.data.get('ram', 0)
        computer.os_version = request.data.get('os_version', '')
        computer.last_seen = timezone.now()
        computer.is_online = True
        computer.save()

        # Log system metrics
        SystemLog.objects.create(
            computer=computer,
            cpu_percent=request.data.get('cpu_percent', 0),
            memory_total=request.data.get('memory_total', 0),
            memory_used=request.data.get('memory_used', 0),
            disk_total=request.data.get('disk_total', 0),
            disk_used=request.data.get('disk_used', 0),
            running_processes=request.data.get('running_processes', 0)
        )

        return Response({'status': 'success'})

    @action(detail=False, methods=['get'])
    def commands(self, request):
        """Endpoint for agents to pull pending commands"""
        hostname = request.query_params.get('hostname')
        if not hostname:
            return Response({'error': 'Hostname is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            computer = Computer.objects.get(hostname=hostname)
        except Computer.DoesNotExist:
            return Response({'error': 'Computer not found'}, status=status.HTTP_404_NOT_FOUND)

        # Get pending commands for this computer
        pending_commands = Command.objects.filter(
            computer=computer,
            status='pending'
        ).values('id', 'type', 'parameters')

        return Response(list(pending_commands))

    @action(detail=False, methods=['post'])
    def command_status(self, request):
        """Endpoint for agents to report command execution status"""
        command_id = request.data.get('command_id')
        status = request.data.get('status')

        if not command_id or not status:
            return Response(
                {'error': 'Command ID and status are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            command = Command.objects.get(id=command_id)
        except Command.DoesNotExist:
            return Response(
                {'error': 'Command not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        command.status = status
        command.completed_at = timezone.now()
        command.save()

        return Response({'status': 'success'})

    @action(detail=True, methods=['post'])
    def send_command(self, request, pk=None):
        """Endpoint for users to send commands to computers"""
        try:
            computer = self.get_object()
        except Computer.DoesNotExist:
            return Response(
                {'error': 'Computer not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        command_type = request.data.get('type')
        parameters = request.data.get('parameters', {})

        if not command_type:
            return Response(
                {'error': 'Command type is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        command = Command.objects.create(
            computer=computer,
            type=command_type,
            parameters=parameters,
            status='pending'
        )

        return Response({
            'id': command.id,
            'status': 'Command queued successfully'
        })

    @action(detail=True, methods=['post'])
    def update_metrics(self, request, pk=None):
        """Update computer system metrics."""
        try:
            computer = self.get_object()
            metrics = computer.metrics or {}
            data = request.data
            
            # Update CPU metrics
            if any(key.startswith('cpu_') for key in data):
                metrics['cpu'] = metrics.get('cpu', {})
                metrics['cpu'].update({
                    'model': data.get('cpu_model'),
                    'speed': data.get('cpu_speed'),
                    'cores': data.get('cpu_cores'),
                    'threads': data.get('cpu_threads'),
                    'architecture': data.get('cpu_architecture'),
                    'percent': data.get('cpu_percent', 0)
                })
            
            # Update memory metrics
            if any(key.startswith('memory_') for key in data):
                metrics['memory'] = metrics.get('memory', {})
                metrics['memory'].update({
                    'total': data.get('memory_total'),
                    'available': data.get('memory_available'),
                    'used': data.get('memory_used'),
                    'percent': data.get('memory_percent', 0)
                })
            
            # Update disk metrics
            if any(key.startswith('disk_') for key in data):
                metrics['disk'] = metrics.get('disk', {})
                metrics['disk'].update({
                    'total': data.get('disk_total'),
                    'free': data.get('disk_free'),
                    'used': data.get('disk_used'),
                    'percent': self._calculate_disk_percent(
                        data.get('disk_total', 0),
                        data.get('disk_used', 0)
                    )
                })

            # Update system information
            computer.device_class = data.get('device_class', computer.device_class)
            computer.model = data.get('model', computer.model)
            computer.os_version = data.get('os_version', computer.os_version)
            computer.logged_in_user = data.get('logged_in_user', computer.logged_in_user)
            computer.hostname = data.get('hostname', computer.hostname)
            computer.boot_time = data.get('boot_time', computer.boot_time)
            computer.system_uptime = data.get('system_uptime', computer.system_uptime)
            
            # Update timestamps
            computer.last_metrics_update = timezone.now()
            if data.get('last_seen'):
                computer.last_seen = timezone.now()
            
            computer.metrics = metrics
            computer.save()
            
            return Response({'status': 'metrics updated'})
            
        except Computer.DoesNotExist:
            return Response({'error': 'Computer not found'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=500)

    @action(detail=True, methods=['post'])
    def execute_remote_command(self, request, pk=None):
        """Execute command directly on remote computer using WinRM"""
        print(f"Execute command endpoint hit with pk={pk}")
        print(f"Request data: {request.data}")

        command = request.data.get('command')
        if not command:
            return Response({'error': 'No command provided'}, status=status.HTTP_400_BAD_REQUEST)

        # List of commands that need PowerShell elevation
        elevated_commands = ['net user', 'net localgroup', 'net group']
        needs_elevation = any(cmd in command.lower() for cmd in elevated_commands)

        try:
            computer = self.get_object()
            username = 'infotech'

            # Configure WinRM session
            session = winrm.Session(
                computer.ip_address,
                auth=(username, settings.INFOTECH_PASSWORD),
                transport='basic',
                server_cert_validation='ignore',
                message_encryption='never',
                operation_timeout_sec=60,
                read_timeout_sec=70
            )

            print(f"Executing command '{command}' on {computer.label} as {username}")
            
            if needs_elevation:
                # Use PowerShell with elevated rights and capture output
                ps_script = f'''
                $outputFile = "$env:TEMP\cmd_output.txt"
                try {{
                    # Run command with elevation and redirect output
                    $pinfo = New-Object System.Diagnostics.ProcessStartInfo
                    $pinfo.FileName = "cmd.exe"
                    $pinfo.Arguments = "/c {command} > `"$outputFile`""
                    $pinfo.Verb = "runas"
                    $pinfo.WindowStyle = "Hidden"
                    $pinfo.UseShellExecute = $true
                    
                    # Start the process and wait
                    $p = [System.Diagnostics.Process]::Start($pinfo)
                    $p.WaitForExit()
                    
                    # Read and return the output
                    if (Test-Path $outputFile) {{
                        $output = Get-Content -Path $outputFile -Raw
                        Remove-Item -Path $outputFile -Force
                        Write-Output $output
                    }} else {{
                        Write-Output "Command executed but produced no output"
                    }}
                }} catch {{
                    Write-Error "Failed to execute elevated command: $_"
                }} finally {{
                    if (Test-Path $outputFile) {{
                        Remove-Item -Path $outputFile -Force -ErrorAction SilentlyContinue
                    }}
                }}
                '''
                print(f"Executing elevated PowerShell script for command: {command}")
                result = session.run_ps(ps_script)
            else:
                # Regular command execution
                print(f"Executing regular command: {command}")
                result = session.run_cmd(command)

            if result.status_code == 0:
                output = result.std_out.decode('utf-8', errors='replace')
                print(f"Command executed successfully")
                return Response({
                    'output': output if output else 'Command executed successfully (no output)',
                    'exit_code': result.status_code
                })
            else:
                error = result.std_err.decode('utf-8', errors='replace')
                print(f"Command failed: {error}")
                return Response({
                    'error': error or 'Command failed with no error message'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except winrm.exceptions.InvalidCredentialsError as e:
            print(f"Authentication failed: {e}", exc_info=True)
            return Response({
                'error': "Authentication failed. Please verify credentials."
            }, status=status.HTTP_401_UNAUTHORIZED)
        except winrm.exceptions.WinRMError as e:
            print(f"WinRM error: {e}", exc_info=True)
            return Response({
                'error': f"WinRM error: {str(e)}"
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as e:
            print(f"Error executing command: {e}", exc_info=True)
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)