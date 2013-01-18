#!/usr/bin/python
# -*- coding: utf-8 -*-

from config import config

assets = {}
import glob, os, os.path, cssmin, jsmin        
assets_dir = os.path.join(config.path, "asset")
for asset, function in [("css", cssmin.cssmin), ("js", None)]:
    asset_dir = os.path.join(assets_dir, asset)
    asset_list = filter(lambda filename: filename.endswith("." + asset) and not filename.startswith("packed-"), sorted(os.listdir(asset_dir)))
    if config.debug:
        assets[asset] = asset_list
    else:
        asset_time = int(max([os.stat(os.path.join(asset_dir, filename)).st_mtime for filename in asset_list]))
        asset_packed = "packed-%d.%s" % (asset_time, asset)
        asset_packed_path = os.path.join(asset_dir, asset_packed)
        if not os.path.exists(asset_packed_path):
            map(os.unlink, glob.glob(os.path.join(asset_dir, "packed-*")))
            open(asset_packed_path, "w").write("\n".join([
                (function if function else lambda x: x)(open(os.path.join(asset_dir, filename)).read())
                for filename in asset_list
            ]))
        assets[asset] = [asset_packed] 
