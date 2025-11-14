import logging
import os
from typing import Dict, Any, Optional
from enum import Enum
from app.classes.ActionReviewNotifier import ActionReviewNotifier
from app.classes.RelationshipAnnounceNotifier import RelationshipAnnounceNotifier
from app.utils.db import get_db

logger = logging.getLogger(__name__)


class ProviderType(Enum):
    """Enumeration of supported data providers."""
    SW_VIZ = "software_viz"
    HAL = "hal"
    SOFTWARE_HERITAGE = "software_heritage"
    UNKNOWN = "unknown"


class NotificationType(Enum):
    """Enumeration of notification types."""
    ACTION_REVIEW = "action_review"
    RELATIONSHIP_ANNOUNCE = "relationship_announce"
    OFFER_ANNOUNCE = "offer_announce"
    UNDEFINED = "undefined"


def detect_provider_from_document_data(doc_id: str) -> ProviderType:
    """
    Detect the provider type from document identifier.

    Args:
        doc_id: The document identifier to analyze

    Returns:
        ProviderType: The detected provider type
    """
    if not doc_id:
        return ProviderType.UNKNOWN

    doc_id_lower = doc_id.lower()

    if doc_id_lower.startswith('oai:hal:'):
        return ProviderType.HAL
    elif doc_id_lower.startswith('swh:'):
        return ProviderType.SOFTWARE_HERITAGE
    else:
        return ProviderType.UNKNOWN


def get_notification_type_for_provider(provider: ProviderType,
                                       document_context: Optional[str] = None) -> NotificationType:
    """
    Determine the appropriate notification type for a given provider.

    Args:
        provider: The provider type
        document_context: Optional context about the document

    Returns:
        NotificationType: The recommended notification type
    """
    if provider == ProviderType.HAL:
        # HAL typically uses ActionReview notifications for peer review
        return NotificationType.ACTION_REVIEW
    elif provider == ProviderType.SOFTWARE_HERITAGE:
        # Software Heritage often uses RelationshipAnnounce for linking
        return NotificationType.RELATIONSHIP_ANNOUNCE
    else:
        # Default to ActionReview for unknown providers
        return NotificationType.ACTION_REVIEW


def extract_notification_data(notification: Dict[str, Any]) -> tuple[str, str]:
    """Extract ID and software name from notification payload."""
    try:
        # Support multiple ID formats
        id_full = notification['object']['object']['id']

        # Extract provider and clean ID
        provider = detect_provider_from_document_data(id_full)

        if provider == ProviderType.HAL:
            doc_id = id_full.replace('oai:HAL:', '')
        else:
            # For other providers, use the ID as-is or apply provider-specific cleaning
            doc_id = id_full

        software_name = notification['object']['object']['sorg:citation']['name']
        return doc_id, software_name
    except KeyError as e:
        logger.error(f"Missing expected key in notification: {e}")
        raise ValueError(f"Invalid notification format: missing {e}")


def accept_notification(notification: Dict[str, Any]) -> bool:
    """
    Handle notification acceptance by marking software as verified by author.

    Args:
        notification: COAR notification payload

    Returns:
        bool: True if update was successful, False otherwise
    """
    try:
        db_manager = get_db()
        document_id, software_name = extract_notification_data(notification)
        logger.info(f"Accepting notification for HAL: {document_id}, Software: {software_name}")
        return db_manager.update_software_with_author_validation(document_id, software_name, True)
    except (ValueError, KeyError) as e:
        logger.error(f"Failed to accept notification: {e}")
        return False


def reject_notification(notification: Dict[str, Any]) -> bool:
    """
    Handle notification rejection by marking software as not verified by author.

    Args:
        notification: COAR notification payload

    Returns:
        bool: True if update was successful, False otherwise
    """
    try:
        db_manager = get_db()
        document_id, software_name = extract_notification_data(notification)
        logger.info(f"Rejecting notification for HAL: {document_id}, Software: {software_name}")
        return db_manager.update_software_with_author_validation(document_id, software_name, False)
    except (ValueError, KeyError) as e:
        logger.error(f"Failed to reject notification: {e}")
        return False


def get_software_notifications(document_id: str) -> list[Dict[str, Any]]:
    """
    Retrieve software notifications for a given HAL document.

    Args:
        hal_filename: HAL filename without extension

    Returns:
        List of notification data for software mentions in the document
    """
    try:
        from app.utils.db import get_db
        db_manager = get_db()
        return db_manager.get_software_notifications(document_id)

    except Exception as e:
        logger.error(f"Failed to retrieve software notifications for {document_id}: {e}")
        return []


def get_notification_config_for_provider(provider: ProviderType) -> Dict[str, str]:
    """
    Get notification configuration for a specific provider.

    Args:
        provider: The provider type

    Returns:
        Dict containing provider-specific configuration
    """
    config = {}

    if provider == ProviderType.HAL:
        hal_token = os.getenv('HAL_TOKEN')
        logger.debug(f"HAL_TOKEN from environment: {'set' if hal_token else 'NOT SET'}")
        config.update({
            'base_url': os.getenv('HAL_BASE_URL', 'https://inria.hal.science'),
            'inbox_url': os.getenv('HAL_INBOX_URL', 'https://inbox-preprod.archives-ouvertes.fr/'),
            'token': hal_token,
        })
    elif provider == ProviderType.SOFTWARE_HERITAGE:
        swh_token = os.getenv('SWH_TOKEN')
        logger.debug(f"SWH_TOKEN from environment: {'set' if swh_token else 'NOT SET'}")
        config.update({
            'base_url': os.getenv('SWH_BASE_URL', 'https://archive.softwareheritage.org'),
            'inbox_url': os.getenv('SWH_INBOX_URL', 'https://inbox.staging.swh.network/'),
            'token': swh_token,
        })
    elif provider == ProviderType.SW_VIZ:
        sw_viz_token = os.getenv('SW_VIZ_TOKEN')
        logger.debug(f"SW_VIZ_TOKEN from environment: {'set' if sw_viz_token else 'NOT SET'}")
        config.update({
            'base_url': os.getenv('SW_VIZ_URL', 'http://coar-viz:8080'),
            'token': sw_viz_token,
        })

    return config


def send_notifications_to_sh(document_id: str, notifications=None) -> int:
    """
    Send COAR notifications specifically to Software Heritage for software mentions.

    Args:
        document_id: document identifier
        notifications: List of notification data for software mentions in the document

    Returns:
        int: Number of notifications successfully sent
    """
    try:
        if not document_id:
            logger.error("Invalid document ID provided")
            return 0

        logger.info(f"Processing Software Heritage notifications for document: {document_id}")

        # Get notification data using the document ID (works for any provider)
        if not notifications:
            logger.warning(f"No software retrieved for {document_id}. "
                           f"No notifications will be sent.")
            return 0

        # Get Software Heritage specific configuration
        config = get_notification_config_for_provider(ProviderType.SOFTWARE_HERITAGE)

        # Send notifications
        success_count = 0
        for notification in notifications:
            notifier = RelationshipAnnounceNotifier(
                document_id,
                "https://datalake.inria.fr",
                "Inria DataLake",
                "https://prod-datadcis.inria.fr/coar/inbox",
                notification['softwareName'],
                None,
                target_id=config['base_url'],
                target_inbox=config['inbox_url'],
                token=config['token']
            )
            response = notifier.send()
            if response:
                success_count += 1

        logger.info(f"Successfully sent {success_count} Software Heritage notifications for {document_id}")
        return success_count

    except Exception as e:
        logger.error(f"Failed to process Software Heritage notifications for {document_id}: {e}")
        return 0


def send_notifications_to_hal(document_id: str, notifications=None) -> int:
    """
    Send COAR notifications to appropriate providers for software mentions in a document.

    Args:
        document_id: document identifier
        notifications: List of notification data for software mentions in the document

    Returns:
        int: Number of notifications successfully sent
    """
    try:
        if not document_id:
            logger.error("Invalid document ID provided")
            return 0

        logger.info(f"Processing notifications for HAL for document: {document_id}")

        # Get notification data using the document ID (works for any provider)
        if not notifications:
            logger.warning(f"No software retrieved for {document_id}. "
                           f"No notifications will be sent.")
            return 0

        # Get provider-specific configuration
        config = get_notification_config_for_provider(ProviderType.HAL)

        # Send notifications
        success_count = 0
        for notification in notifications:
            notifier = ActionReviewNotifier(
                document_id,
                actor_id="https://datalake.inria.fr",
                actor_name="Inria DataLake",
                origin_inbox="https://prod-datadcis.inria.fr/coar/inbox",
                software_name=notification['softwareName'],
                software_repo=None,
                mention_type="software",
                mention_context=notification['contexts'],
                target_id=config['base_url'],  # target_id
                target_inbox=config['inbox_url'],  # target_inbox
                token=config['token']
            )
            response = notifier.send()
            if response:
                success_count += 1

        logger.info(f"Successfully sent {success_count} notifications for {ProviderType.HAL.value}:{document_id}")
        return success_count

    except Exception as e:
        logger.error(f"Failed to process notifications for document_id {document_id}: {e}")
        return 0


def send_validation_to_viz(document_id: str, software_name: str, accepted: bool = True):
    """
    Send validation information to Software Viz service.

    Args:
        document_id: HAL document identifier
        software_name: Software name
        accepted: Verification status

    Returns:
        bool: True if sent successfully, False otherwise
    """

    config = get_notification_config_for_provider(ProviderType.SW_VIZ)

    endpoint = "accepted_notification" if accepted else "rejected_notification"
    url = f"{config['base_url']}/api/{endpoint}/{document_id}/{software_name}"
    headers = {
        'Content-Type': 'application/json'
    }

    if config['token']:
        headers['Authorization'] = f'Bearer {config["token"]}'

    import requests
    try:
        response = requests.post(
            url,
            headers=headers,
            timeout=5
        )
        response.raise_for_status()
        logger.info(f"Successfully sent {endpoint} notification to {url}")
        return response
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send notification: {e}")
        return False
    except Exception as e:
        logger.error(f"Error sending validation to Software Viz: {e}")
        return False