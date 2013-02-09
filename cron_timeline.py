#!/usr/bin/python
# -*- coding: utf-8 -*-

if __name__ == "__main__":
    from db import db
    from kv import storage as kv_storage
    from controller.content.model import ContentItem
    from controller.content.feed import all as feeds
    from controller.content.type import all as content_types
 
    for type in feeds["timeline"]["types"]:
        provider = content_types[type]["type"].get_provider()
        if provider is None:
            continue
        if not provider.available():
            continue

        item_ids = []
        for item in provider.provide():
            id = str(item.id)
            item_ids.append(id)

            content_item = db.query(ContentItem).filter_by(type=type, type_key=id).first()
            if content_item is None:
                content_item = ContentItem()
                content_item.type = type
                content_item.type_key = id
                content_item.created_at = item.created_at
                content_item.data = item.data

                for kv_directory in item.kv:
                    kv = item.kv[kv_directory]
                    for k, v in kv() if callable(kv) else kv:
                        if k not in kv_storage[kv_directory]:
                            kv_storage[kv_directory][k] = v() if callable(v) else v

                db.add(content_item)
                db.flush()

                provider.on_item_inserted(content_item)

            content_item.permissions = content_types[type].get("permissions", 0)

        for content_item in db.query(ContentItem).filter(ContentItem.type == type, ContentItem.permissions != ContentItem.permissions_DELETED).order_by(-ContentItem.created_at)[:len(item_ids)]:
            if content_item.type_key not in item_ids and provider.is_not_actual_item(content_item):
                content_item.permissions = ContentItem.permissions_DELETED
    
        db.flush()
