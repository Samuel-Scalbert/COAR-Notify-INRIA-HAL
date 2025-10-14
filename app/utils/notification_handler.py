import logging
import os
from typing import Dict, Any, List, Optional
from enum import Enum
from werkzeug.datastructures import FileStorage
from app.classes.ActionReviewNotifier import ActionReviewNotifier
from app.classes.RelationshipAnnounceNotifier import RelationshipAnnounceNotifier

logger = logging.getLogger(__name__)


class ProviderType(Enum):
    """Enumeration of supported data providers."""
    HAL = "hal"
    SOFTWARE_HERITAGE = "software_heritage"
    ZENODO = "zenodo"
    GITHUB = "github"
    UNKNOWN = "unknown"


class NotificationType(Enum):
    """Enumeration of notification types."""
    ACTION_REVIEW = "action_review"
    RELATIONSHIP_ANNOUNCE = "relationship_announce"
    OFFER_ANNOUNCE = "offer_announce"
    UNDEFINED = "undefined"


def detect_provider_from_filename(filename: str) -> ProviderType:
    """
    Detect the provider type from filename patterns.

    Args:
        filename: The filename to analyze

    Returns:
        ProviderType: The detected provider type
    """
    if not filename:
        return ProviderType.UNKNOWN

    filename_lower = filename.lower()

    if any(pattern in filename_lower for pattern in ['hal-', 'oai:hal:', '.hal.']):
        return ProviderType.HAL
    elif any(pattern in filename_lower for pattern in ['swh-', 'softwareheritage', '.swh.']):
        return ProviderType.SOFTWARE_HERITAGE
    elif any(pattern in filename_lower for pattern in ['zenodo-', '.zenodo.']):
        return ProviderType.ZENODO
    elif any(pattern in filename_lower for pattern in ['github-', '.github.']):
        return ProviderType.GITHUB
    else:
        return ProviderType.UNKNOWN


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
    elif 'zenodo' in doc_id_lower:
        return ProviderType.ZENODO
    elif 'github' in doc_id_lower:
        return ProviderType.GITHUB
    else:
        return ProviderType.UNKNOWN


def get_notification_type_for_provider(provider: ProviderType, document_context: Optional[str] = None) -> NotificationType:
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
    elif provider == ProviderType.ZENODO:
        # Zenodo may use ActionReview for citation/review
        return NotificationType.ACTION_REVIEW
    elif provider == ProviderType.GITHUB:
        # GitHub often uses RelationshipAnnounce for repository linking
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


def update_software_verification(hal_id: str, software_name: str, verification_status: bool) -> bool:
    """
    Update software verification status in database.

    Args:
        hal_id: HAL identifier without 'oai:HAL:' prefix
        software_name: Normalized software name
        verification_status: True for accepted, False for rejected
    Returns:
        bool: True if update was successful, False otherwise
    """
    try:
        from app.utils.db import get_db
        db_manager = get_db()
        return db_manager.update_software_verification(hal_id, software_name, verification_status)

    except Exception as e:
        logger.error(f"Failed to update software verification: {e}")
        return False


def accept_notification(notification: Dict[str, Any]) -> bool:
    """
    Handle notification acceptance by marking software as verified by author.

    Args:
        notification: COAR notification payload

    Returns:
        bool: True if update was successful, False otherwise
    """
    try:
        hal_id, software_name = extract_notification_data(notification)
        logger.info(f"Accepting notification for HAL: {hal_id}, Software: {software_name}")
        return update_software_verification(hal_id, software_name, True)
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
        hal_id, software_name = extract_notification_data(notification)
        logger.info(f"Rejecting notification for HAL: {hal_id}, Software: {software_name}")
        return update_software_verification(hal_id, software_name, False)
    except (ValueError, KeyError) as e:
        logger.error(f"Failed to reject notification: {e}")
        return False



def get_software_notifications(hal_filename: str) -> list[Dict[str, Any]]:
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
        return db_manager.get_software_notifications(hal_filename)

    except Exception as e:
        logger.error(f"Failed to retrieve software notifications for {hal_filename}: {e}")
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
        config.update({
            'base_url': os.getenv('HAL_BASE_URL', 'https://inria.hal.science'),
            'inbox_url': os.getenv('HAL_INBOX_URL', 'https://inbox-preprod.archives-ouvertes.fr/'),
        })
    elif provider == ProviderType.SOFTWARE_HERITAGE:
        config.update({
            'base_url': os.getenv('SWH_BASE_URL', 'https://archive.softwareheritage.org'),
            'inbox_url': os.getenv('SWH_INBOX_URL', 'https://inbox.softwareheritage.org'),
        })
    elif provider == ProviderType.ZENODO:
        config.update({
            'base_url': os.getenv('ZENODO_BASE_URL', 'https://zenodo.org'),
            'inbox_url': os.getenv('ZENODO_INBOX_URL', 'https://inbox.zenodo.org'),
        })
    elif provider == ProviderType.GITHUB:
        config.update({
            'base_url': os.getenv('GITHUB_BASE_URL', 'https://github.com'),
            'inbox_url': os.getenv('GITHUB_INBOX_URL', 'https://inbox.github.com'),
        })
    else:
        # Default configuration
        config.update({
            'base_url': os.getenv('DEFAULT_BASE_URL', 'http://127.0.0.1:5500/'),
            'inbox_url': os.getenv('DEFAULT_INBOX_URL', 'http://127.0.0.1:5500/inbox'),
        })

    # Add development URLs
    config.update({
        'dev_base_url': os.getenv('DEV_BASE_URL', 'http://127.0.0.1:5500/'),
        'dev_inbox_url': os.getenv('DEV_INBOX_URL', 'http://127.0.0.1:5500/inbox')
    })

    return config


def get_notifier_class_for_notification_type(notification_type: NotificationType):
    """
    Get the appropriate notifier class for a notification type.

    Args:
        notification_type: The type of notification

    Returns:
        The notifier class to use
    """
    if notification_type == NotificationType.ACTION_REVIEW:
        return ActionReviewNotifier
    elif notification_type == NotificationType.RELATIONSHIP_ANNOUNCE:
        return RelationshipAnnounceNotifier
    else:
        # Default to ActionReview
        return ActionReviewNotifier


def send_notification(notifier_class, document_id: str, notification_data: Dict[str, Any],
                     config: Dict[str, str], provider: ProviderType) -> bool:
    """
    Send a notification using the specified notifier class.

    Args:
        notifier_class: The notifier class to instantiate
        document_id: Document identifier (provider-specific format)
        notification_data: Notification payload data
        config: Configuration dictionary with URLs
        provider: The provider type for context

    Returns:
        bool: True if notification was sent successfully
    """
    try:
        if notifier_class == ActionReviewNotifier:
            notifier = notifier_class(
                document_id,
                notification_data['softwareName'],
                None,
                notification_data['maxDocumentAttribute'],
                notification_data['contexts'],
                config['base_url'],
                config['inbox_url']
            )
        else:  # RelationshipAnnounceNotifier
            notifier = notifier_class(
                document_id,
                notification_data['softwareName'],
                None,
                config['dev_base_url'],
                config['dev_inbox_url']
            )

        response = notifier.send()
        logger.info(f"Sent {notifier_class.__name__} notification for {provider.value}:{document_id} "
                   f"-> {notification_data['softwareName']}")
        return True

    except Exception as e:
        logger.error(f"Failed to send {notifier_class.__name__} notification for {provider.value}: {e}")
        return False


def send_notifications_to_sh(file: FileStorage) -> int:
    """
    Send COAR notifications specifically to Software Heritage for software mentions.

    Args:
        file: Uploaded file object containing software metadata

    Returns:
        int: Number of notifications successfully sent
    """
    try:
        # Extract document identifier from file
        if not file.filename:
            logger.error("Invalid filename provided")
            return 0

        # Clean filename to get document ID (SWH-specific format)
        document_id = file.filename.replace('.software.json', '').replace('.json', '')
        if not document_id:
            logger.error("Could not extract document ID from filename")
            return 0

        logger.info(f"Processing Software Heritage notifications for document: {document_id}")

        # Get notification data using the document ID
        notifications = get_software_notifications(document_id)
        if not notifications:
            logger.warning(f"No software notifications found for {document_id}")
            return 0

        # Software Heritage typically uses RelationshipAnnounce notifications
        notification_type = NotificationType.RELATIONSHIP_ANNOUNCE
        notifier_class = get_notifier_class_for_notification_type(notification_type)

        # Get Software Heritage specific configuration
        config = get_notification_config_for_provider(ProviderType.SOFTWARE_HERITAGE)

        # Send notifications
        success_count = 0
        for notification in notifications:
            # Send to Software Heritage production inbox
            if send_notification(notifier_class, document_id, notification, config, ProviderType.SOFTWARE_HERITAGE):
                success_count += 1

            # Send to development environment (for testing)
            send_notification(RelationshipAnnounceNotifier, document_id, notification, config, ProviderType.SOFTWARE_HERITAGE)

        logger.info(f"Successfully sent {success_count} Software Heritage notifications for {document_id}")
        return success_count

    except Exception as e:
        logger.error(f"Failed to process Software Heritage notifications for file {file.filename}: {e}")
        return 0

def send_notifications_to_hal(file: FileStorage) -> int:
    """
    Send COAR notifications to appropriate providers for software mentions in a document.

    Args:
        file: Uploaded file object containing software metadata

    Returns:
        int: Number of notifications successfully sent
    """
    try:
        # Extract document identifier from file
        if not file.filename:
            logger.error("Invalid filename provided")
            return 0

        # Clean filename to get document ID
        document_id = file.filename.replace('.software.json', '').replace('.json', '')
        if not document_id:
            logger.error("Could not extract document ID from filename")
            return 0

        # Detect provider from filename
        provider = detect_provider_from_filename(file.filename)
        logger.info(f"Processing notifications for {provider.value} document: {document_id}")

        # Get notification data using the document ID (works for any provider)
        notifications = get_software_notifications(document_id)
        if not notifications:
            logger.warning(f"No software notifications found for {document_id}")
            return 0

        # Determine appropriate notification type for this provider
        notification_type = get_notification_type_for_provider(provider)
        notifier_class = get_notifier_class_for_notification_type(notification_type)

        # Get provider-specific configuration
        config = get_notification_config_for_provider(provider)

        # Send notifications
        success_count = 0
        for notification in notifications:
            # Send to provider's production inbox
            if send_notification(notifier_class, document_id, notification, config, provider):
                success_count += 1

            # Send to development environment (for testing)
            send_notification(RelationshipAnnounceNotifier, document_id, notification, config, provider)

        logger.info(f"Successfully sent {success_count} notifications for {provider.value}:{document_id}")
        return success_count

    except Exception as e:
        logger.error(f"Failed to process notifications for file {file.filename}: {e}")
        return 0



