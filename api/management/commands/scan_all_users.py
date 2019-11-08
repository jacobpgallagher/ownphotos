from django.core.management.base import BaseCommand
from api.models import User
from api.directory_watcher import scan_photos_helper

class Command(BaseCommand):
    help = "Scan all the users's directories"

    def handle(self, *args, **kwargs):
        for user in User.objects.exclude(scan_directory=''):
            scan_photos_helper(user)
