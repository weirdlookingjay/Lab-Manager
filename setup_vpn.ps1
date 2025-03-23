# Requires elevation (Run as Administrator)
#Requires -Version 5.1

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Error "This script must be run as Administrator. Right-click PowerShell and select 'Run as Administrator'."
    exit 1
}

# VPN Configuration Parameters
$vpnName = "AW VPN"
$serverAddress = "azuregateway-19ad0078-3210-446e-a3dd-9194ee3de4fe-da3409ff72ba.vpn.azure.com"
$dnsSuffix = "corp.americaworks.com"
$tunnelType = "Automatic" # Windows built-in VPN will automatically select the best protocol
$authMethod = "MSChapv2"
$encryptionLevel = "Required"

# Remove existing VPN connection with the same name if it exists
Get-VpnConnection -Name $vpnName -ErrorAction SilentlyContinue | Remove-VpnConnection -Force -ErrorAction SilentlyContinue

# Add the VPN connection
Add-VpnConnection -Name $vpnName `
    -ServerAddress $serverAddress `
    -TunnelType $tunnelType `
    -EncryptionLevel $encryptionLevel `
    -AuthenticationMethod $authMethod `
    -RememberCredential $true `
    -SplitTunneling $true `
    -PassThru

# Wait for the network adapter to be created
Start-Sleep -Seconds 2

# Get the network adapter for the VPN
$vpnAdapter = Get-NetAdapter | Where-Object { $_.Name -like "*$vpnName*" }

if ($vpnAdapter) {
    # Configure DNS suffix for the VPN adapter
    Set-DnsClient -InterfaceIndex $vpnAdapter.ifIndex -ConnectionSpecificSuffix $dnsSuffix
    
    Write-Host "VPN connection '$vpnName' has been created successfully!"
    Write-Host "DNS suffix has been set to '$dnsSuffix'"
    Write-Host "`nImportant Notes:"
    Write-Host "1. The VPN is now configured and ready to use"
    Write-Host "2. To connect, click on the network icon in the system tray and select '$vpnName'"
    Write-Host "3. DNS suffix has been pre-configured to prevent connectivity issues"
} else {
    Write-Error "Failed to find the VPN adapter. Please try running the script again."
}
