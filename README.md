# AHAB

## Overview
The purpose of this repo is to serve as a place to maintain my more consolidated MKE/MSR/MCR tooling. Items
will be added as I convert my more loosely connected scripts into actual tools consumable by others.

As for the name. I'm hunting whales.

## Tools

### [msr-disk-usage](./msr-disk-usage)

  This tool is to assist people with analyzing the footprint of the registry images to reduce size and bloat.

### [msr-unknown-blob](./msr-unknown-blob)

  A tool for tracing "unknown blob" errors.

### mke-config

This tool provides a wrapper for adjusting various configuration settings in MKE (via the API). Note that the config options
it supports will exapand as needed so functionality may be limited initially.


### msr-scan-all-tags

A customer may need to trigger new scanning process (for example, if we drop the scanned_images/scanned_layers) for all tags. By default
the API endpoint which does this only does it for repos where scanning has already been run/configured. For large installations it is impractical
to set this up by hand. Only other ways to launch a scan are to click the UI button or repush all images (if scan on push is enabled).

