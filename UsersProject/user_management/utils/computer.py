from django.http import Http404
from ..models import Computer

def get_computer_or_404(computer_id):
    """
    Get a computer by ID or raise Http404 if not found.
    Also verifies that the computer is online based on the 30-minute threshold.
    """
    try:
        computer = Computer.objects.get(id=computer_id)
        if not computer.is_online():
            raise Http404("Computer is offline")
        return computer
    except Computer.DoesNotExist:
        raise Http404("Computer not found")
