from api.models import Media, User
import requests
import numpy as np
from django.db.models import Q
from ownphotos.settings import IMAGE_SIMILARITY_SERVER

import logging
logger = logging.getLogger(__name__)

def search_similar_image(user,media):
    # Skip medias that haven't been processed
    if not media.encoding:
        return

    if type(user) == int:
        user_id = user
    else:
        user_id = user.id

    image_embedding = np.array(
        np.frombuffer(bytes.fromhex(media.encoding)), dtype=np.float32)
    post_data = {
        "user_id":user_id,
        "image_embedding":image_embedding.tolist()
    }
    res = requests.post(IMAGE_SIMILARITY_SERVER+'/search/',json=post_data)
    if res.status_code==200:
        return res.json()
    else:
        logger.error('error retrieving similar medias to {} belonging to user {}'.format(media.pk, user.username))
        return

def build_image_similarity_index(user):
    logger.info('builing similarity index for user {}'.format(user.username))
    medias = Media.objects.filter(Q(owner=user) | Q(owner__collaborators=user)).exclude(encoding=None).only('encoding')

    image_hashes = []
    image_embeddings = []

    for media in medias:
        image_hashes.append(media.pk)
        image_embedding = np.array(
            np.frombuffer(bytes.fromhex(media.encoding)), dtype=np.float32)
        image_embeddings.append(image_embedding.tolist())

    post_data = {
        "user_id":user.id,
        "image_hashes":image_hashes,
        "image_embeddings":image_embeddings
    }
    res = requests.post(IMAGE_SIMILARITY_SERVER+'/build/',json=post_data)
    return res.json()
