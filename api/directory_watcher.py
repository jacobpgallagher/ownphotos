import os
import datetime
import hashlib
import pytz
import time
import traceback
from joblib import Parallel, delayed
import multiprocessing

from api.models import (Photo, Video, Media, Person, LongRunningJob)

from tqdm import tqdm
from config import image_dirs

import api.util as util
from api import video_utils
from api.image_similarity import build_image_similarity_index

import ipdb
from django_rq import job
import time
import numpy as np
import rq


from django.db.models import Q
from django.db.utils import IntegrityError
from django.db import transaction
import json

import logging
logger = logging.getLogger(__name__)


def is_new_image(existing_hashes, image_path):
    hash_md5 = hashlib.md5()
    with open(image_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    image_hash = hash_md5.hexdigest()
    if image_hash not in existing_hashes or (
            not Photo.objects.filter(image_path=image_path).exists()):
        return image_path
    return

@transaction.atomic
def handle_new_video(user, video_path, job_id):
    try:
        start = datetime.datetime.now()

        hash_md5 = hashlib.md5()
        with open(video_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)

        video_hash = hash_md5.hexdigest() + str(user.id)
        elapsed = (datetime.datetime.now() - start).total_seconds()
        logger.debug('Generating md5 took %.2f', elapsed)

        video_exists = Video.objects.filter(Q(video_hash = video_hash) | Q(video_path=video_path)).exists()

        if video_exists:
            logger.warning('job %s: file %s exists already', job_id, video_path)
            return

        # Do the meta
        meta = video_utils.get_video_metadata(video_path)


        # Find Media, if exists
        image_subpath = '.'.join(video_path.split('.')[:-1])
        medias = list(Media.objects.filter(photo__image_path__startswith=image_subpath).filter(owner=user))

        created = False
        if len(medias) == 1:
            media = medias[0]
        else:
            if len(medias) > 1:
                logging.warning('Multiple Medias for video %s', video_path)

            lat, lng, _ = video_utils.extract_lat_lng_from_meta(meta)
            media = Media.objects.create(
                owner=user,
                meta_timestamp = video_utils.extract_create_time_from_meta(meta),
                meta_gps_lat=lat,
                meta_gps_lon=lng,
            )
            created = True


        video = Video.objects.create(
            video_path=video_path,
            video_hash=video_hash,
            media=media,
            meta_json=meta,
        )

        if created:
            # Thumbnails
            start = datetime.datetime.now()
            media._generate_thumbnail()
            elapsed = (datetime.datetime.now() - start).total_seconds()
            logger.debug('Generating thumbnails took %.2f', elapsed)


    except Exception as e:
        try:
            logger.exception("job {}: could not load video {}. reason: {}".format(
                job_id,video_path, str(e)))
        except:
            logger.exception("job {}: could not load video {}".format(job_id,image_path))
        raise


@transaction.atomic
def handle_new_image(user, image_path, job_id):
    if image_path.lower().endswith('.jpg'):
        try:
            elapsed_times = {
                'md5':None,
                'thumbnails':None,
                'captions':None,
                'image_save':None,
                'exif':None,
                'geolocation':None,
                'faces':None,
                'album_place':None,
                'album_date':None,
                'album_thing':None,
                'im2vec':None,
                'media': None,
            }

            img_abs_path = image_path
            logger.info('job {}: handling image {}'.format(job_id,img_abs_path))

            start = datetime.datetime.now()
            hash_md5 = hashlib.md5()
            with open(img_abs_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            image_hash = hash_md5.hexdigest() + str(user.id)
            elapsed = (datetime.datetime.now() - start).total_seconds()
            elapsed_times['md5'] = elapsed
            logger.debug('generating md5 took %.2f, image_hash: %s' %
                        (elapsed, image_hash))

            photo_exists = Photo.objects.filter(
                Q(image_hash=image_hash)
                | Q(image_path=image_path)).exists()

            if not photo_exists:


                # Find Media, if exists
                video_subpath = '.'.join(image_path.split('.')[:-1])
                medias = list(Media.objects.filter(video__video_path__startswith(video_subpath)).filter(owner=user))

                created = False
                if len(medias) == 1:
                    media = medias[0]
                else:
                    if len(medias) > 1:
                        logging.warning('Multiple Medias for video %s', video_path)

                    media = Media.objects.create(
                        owner=user,
                    )
                    created = True


                photo = Photo.objects.create(
                    image_path=img_abs_path,
                    owner=user,
                    image_hash=image_hash,
                    added_on=datetime.datetime.now().replace(tzinfo=pytz.utc),
                    geolocation_json={},
                    media=media)
                #photo._generate_md5()

                start = datetime.datetime.now()
                photo._generate_thumbnail()
                elapsed = (datetime.datetime.now() - start).total_seconds()
                elapsed_times['thumbnails'] = elapsed
                logger.debug('thumbnail get took %.2f' % elapsed)

                start = datetime.datetime.now()
                photo._generate_captions()
                elapsed = (datetime.datetime.now() - start).total_seconds()
                elapsed_times['captions'] = elapsed
                logger.debug('caption generation took %.2f' % elapsed)

#                 start = datetime.datetime.now()
#                 photo._save_image_to_db()
#                 elapsed = (datetime.datetime.now() - start).total_seconds()
#                 elapsed_times['image_save'] = elapsed
#                 logger.debug('image save took %.2f' % elapsed)

                start = datetime.datetime.now()
                photo._extract_exif()
                photo.save()
                elapsed = (datetime.datetime.now() - start).total_seconds()
                elapsed_times['exif'] = elapsed
                logger.debug('exif extraction took %.2f' % elapsed)

                start = datetime.datetime.now()
                photo._geolocate_mapbox()
                photo.save()
                elapsed = (datetime.datetime.now() - start).total_seconds()
                elapsed_times['geolocation'] = elapsed
                logger.debug('geolocation took %.2f' % elapsed)

                start = datetime.datetime.now()
                photo._add_to_album_place()
                photo.save()
                elapsed = (datetime.datetime.now() - start).total_seconds()
                elapsed_times['album_place'] = elapsed
                logger.debug('add to AlbumPlace took %.2f' % elapsed)

                start = datetime.datetime.now()
                photo._extract_faces()
                elapsed = (datetime.datetime.now() - start).total_seconds()
                elapsed_times['faces'] = elapsed
                logger.debug('face extraction took %.2f' % elapsed)

                start = datetime.datetime.now()
                photo._add_to_album_date()
                elapsed = (datetime.datetime.now() - start).total_seconds()
                elapsed_times['album_date'] = elapsed
                logger.debug('adding to AlbumDate took %.2f' % elapsed)

                start = datetime.datetime.now()
                photo._add_to_album_thing()
                elapsed = (datetime.datetime.now() - start).total_seconds()
                elapsed_times['album_thing'] = elapsed
                logger.debug('adding to AlbumThing took %.2f' % elapsed)

                start = datetime.datetime.now()
                photo._im2vec()
                elapsed = (datetime.datetime.now() - start).total_seconds()
                elapsed_times['im2vec'] = elapsed
                logger.debug('im2vec took %.2f' % elapsed)


                # Copy photo stuff to media
                start = datetime.datetime.now()

                photo.media.meta_gpa_lat = photo.exif_gps_lat
                photo.media.meta_gpa_lon = photo.exif_gps_lon
                photo.media.meta_timestamp = photo.exif_timestamp

                photo.media._generate_thumbnail()
                photo.media.save()

                elapsed = (datetime.datetime.now() - start).total_seconds()
                elapsed_times['media'] = elapsed
                logger.debug('copy/generating media data took %.2f' % elapsed)

                logger.info("job {}: image processed: {}, elapsed: {}".format(job_id,img_abs_path,json.dumps(elapsed_times)))


                if photo.image_hash == '':
                    logger.warning("job {}: image hash is an empty string. File path: {}".format(job_id,photo.image_path))
            else:
                logger.warning("job {}: file {} exists already".format(job_id,image_path))

        except Exception as e:
            try:
                logger.exception("job {}: could not load image {}. reason: {}".format(
                    job_id,image_path, str(e)))
            except:
                logger.exception("job {}: could not load image {}".format(job_id,image_path))
            raise
    return


@job
def scan_photos(user):
    job_id = rq.get_current_job().id

    if LongRunningJob.objects.filter(job_id=job_id).exists():
        lrj = LongRunningJob.objects.get(job_id=job_id)
        lrj.started_at = datetime.datetime.now().replace(tzinfo=pytz.utc)
        lrj.save()
    else:
        try:
            lrj = LongRunningJob.objects.create(
                started_by=user,
                job_id=job_id,
                queued_at=datetime.datetime.now().replace(tzinfo=pytz.utc),
                started_at=datetime.datetime.now().replace(tzinfo=pytz.utc),
                job_type=LongRunningJob.JOB_SCAN_PHOTOS)
            lrj.save()
        except IntegrityError:
            lrj = LongRunningJob.objects.get(job_id=job_id)
            lrj.started_at = datetime.datetime.now().replace(tzinfo=pytz.utc)
            lrj.save()


    return scan_photos_helper(user, lrj)

def scan_photos_helper(user, lrj=None):
    if lrj:
        job_id=lrj.id
    else:
        job_id=None


    added_photo_count = 0
    already_existing_photo = 0

    try:
        image_paths = []
        video_paths_to_add = set()

        for dp, dn, fn in os.walk(user.scan_directory):
            dn[:] = [d for d in dn if not d.startswith('.')]
            fn[:] = [f for f in fn if not f.startswith('.')]
            for f in fn:
                image_paths.append(os.path.join(dp, f))
                if f.lower().endswith('.mov'):
                    video_paths_to_add.add(os.path.join(dp, f))

        image_paths = [
            p for p in image_paths
            if p.lower().endswith('.jpg') and 'thumb' not in p.lower()
        ]
        image_paths.sort()


        # existing_hashes = [p.image_hash for p in Photo.objects.all()]

        # Create a list with all images whose hash is new or they do not exist in the db
        image_paths_to_add = []
        for image_path in image_paths:
            if not Photo.objects.filter(image_path=image_path).exists():
                image_paths_to_add.append(image_path)

        video_paths_to_subtract = set(Video.objects.filter(media__owner=user).values_list('video_path', flat=True))

        video_paths_to_add = sorted(list(video_paths_to_add.difference(video_paths_to_subtract)))

        to_add_count = len(image_paths_to_add) + len(video_paths_to_add)
        for idx, image_path in enumerate(image_paths_to_add):
            handle_new_image(user, image_path, job_id)
            if lrj is not None:
                lrj.result = {
                    'progress': {
                        "current": idx + 1,
                        "target": to_add_count
                    }
                }
                lrj.save()


        for idx, video_path in enumerate(video_paths_to_add):
            handle_new_video(user, video_path, job_id)
            if lrj is not None:
                lrj.result = {
                    'progress': {
                        "current": len(image_paths_to_add) + idx,
                        "target": to_add_count
                    }
                }
                lrj.save()
        '''
        image_paths_to_add = Parallel(n_jobs=multiprocessing.cpu_count(), backend="multiprocessing")(delayed(is_new_image)(existing_hashes, image_path) for image_path in tqdm(image_paths))
        image_paths_to_add = filter(None, image_paths_to_add)
        Parallel(n_jobs=multiprocessing.cpu_count(), backend="multiprocessing")(delayed(handle_new_image)(user, image_path) for image_path in tqdm(image_paths_to_add))
        '''

        logger.info("Added {} photos".format(len(image_paths_to_add)))
        build_image_similarity_index(user)

        if lrj is not None:
            lrj = LongRunningJob.objects.get(job_id=rq.get_current_job().id)
            lrj.finished = True
            lrj.finished_at = datetime.datetime.now().replace(tzinfo=pytz.utc)
            prev_result = lrj.result
            next_result = prev_result
            next_result['new_photo_count'] = added_photo_count
            lrj.result = next_result
            lrj.save()
    except Exception as e:
        if lrj is not None:
            logger.exception(str(e))
            lrj = LongRunningJob.objects.get(job_id=rq.get_current_job().id)
            lrj.finished = True
            lrj.failed = True
            lrj.finished_at = datetime.datetime.now().replace(tzinfo=pytz.utc)
            prev_result = lrj.result
            next_result = prev_result
            next_result['new_photo_count'] = 0
            lrj.result = next_result
            lrj.save()
        raise
    return {"new_photo_count": added_photo_count, "status": True}
