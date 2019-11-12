from django.core.management.base import BaseCommand
from django.db.models import Q
from api.models import Photo
from api.directory_watcher import scan_photos_helper
import datetime
import logging
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Scan all the users's directories"

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, required=False, default=None, help='limit the number of photos to process')
        parser.add_argument('--only_null', action='store_true', help='only photos with null (unprocessed) variables')

    def handle(self, *args, **options):

        qs = Photo.objects.all()
        if options['only_null']:
            qs = qs.filter(Q(captions_json__is=True) | Q(encoding__isnull=True))
        if options['limit']:
            qs = qs[:options['limit']]

        photo_count = qs.count()
        for idx, photo in enumerate(qs):
            start = datetime.datetime.now()
            photo._generate_captions()
            elapsed_caption = (datetime.datetime.now() - start).total_seconds()

            start = datetime.datetime.now()
            photo._im2vec()
            elapsed_im2vec = (datetime.datetime.now() - start).total_seconds()

            logger.info("Processing %s/%s time: caption: %.2f im2vec: %.2f", idx + 1, photo_count, elapsed_caption, elapsed_im2vec)
