from homeassistant.core import callback
import logging

_LOGGER = logging.getLogger(__name__)

""" Helps us process NHC2 entities """


def nhc2_entity_processor(hass, config_entry, async_add_entities, key, obj_create):
    @callback
    def process_entities(entities):
        # Collect a list of active UUIDs
        active_uuids = list(map(lambda x: x.uuid, hass.data[key][config_entry.entry_id]))
        _LOGGER.debug('Active UUIDs: %s', ', '.join(active_uuids))

        # Sort out existing and new entities
        new_entities, existing_entities = [], []
        for entity in entities:
            (new_entities, existing_entities)[entity.uuid in active_uuids].append(entity)

        _LOGGER.debug('Existing UUIDs: %s', ', '.join(list(map(lambda x: x.uuid, existing_entities))))
        _LOGGER.debug('New UUIDs: %s', ', '.join(list(map(lambda x: x.uuid, new_entities))))

        # Process the new entities
        new_hass_entities = []
        for entity in new_entities:
            new_entity = obj_create(entity)
            hass.data[key][config_entry.entry_id].append(new_entity)
            new_hass_entities.append(new_entity)
        async_add_entities(new_hass_entities)
        _LOGGER.debug('Adding new entities done.')

        # Process the existing entities (update)
        for entity in existing_entities:
            entity_to_update = \
                next(filter((
                    lambda x: x.uuid == entity.uuid),
                    hass.data[key][config_entry.entry_id]), None)
            entity_to_update.nhc2_update(entity)
        _LOGGER.debug('Update done.')

        # List UUIDs that should be removed
        uuids_from_entities = list(map(lambda x: x.uuid, entities))
        uuids_to_remove = [i for i in uuids_from_entities + active_uuids if i not in uuids_from_entities]
        _LOGGER.debug('UUIDs to remove: %s', ', '.join(uuids_to_remove))

        # Remove entities (the need be removed)
        for uuid_to_remove in uuids_to_remove:
            entity_to_remove = next(filter((
                lambda x: x.uuid == uuid_to_remove),
                hass.data[key][config_entry.entry_id]), None)
            hass.add_job(entity_to_remove.async_remove())
            hass.data[key][config_entry.entry_id].remove(entity_to_remove)
        _LOGGER.debug('Removals done.')

    return process_entities
