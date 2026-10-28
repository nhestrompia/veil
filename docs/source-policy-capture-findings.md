# Capture routes after physical use

Two additional capture routes ran against the same physically calibrated browser process. Its PID, trial, and executable hash stayed unchanged. The probe binary also stayed unchanged.

| Route | Readable reference | Restricted browser |
| --- | --- | --- |
| ScreenCaptureKit display filter that includes only the target window | Marker recovered in all three images | Three identical black images. No marker recovered. |
| System screenshot command for the exact target window | Marker recovered in all three images | All three commands failed. Results remain inconclusive. |

Direct inspection of the first display image confirmed a black image with no page content. The display filter excludes other windows. This is not an unfiltered display-compositor capture.

The [saved evidence](evidence/source-policy-capture-results.json) retains route metadata, image hashes, permissions, binary identities, and reference cleanup. All six reference processes passed cleanup. No input ran and no new website submission appeared.

## Controller

The new capture controller resolves all image paths before probe launch. It refuses candidate capture when the matched reference cannot recover its marker. It verifies the unchanged browser and probe, and stops if reference cleanup fails. Three checks cover failed captures, failed marker controls, and cleanup failure.

## Limits

A failed screenshot command does not prove that all system screenshot paths deny content. The filtered display result does not replace an unfiltered display, stream, remote-sharing, or OS-version control.

These tests strengthen the observation record for the physically usable build. They do not establish general capture protection or agent-free browsing. Physical keyboard observation remains a separate open route.
