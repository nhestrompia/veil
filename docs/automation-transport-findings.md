# Automation transport checks after desktop recovery

Playwright 1.64.0 completed three independent website actions through an isolated headless Chromium control. Each action disclosed the disposable page marker and reached the loopback oracle.

The rebuilt AgentFreeBrowser, InspectableControl, and DeviceKeyboardExperiment each received two attachment attempts. Chromium DevTools Protocol attachment found no endpoint. A direct Playwright WebKit launch did not establish its expected inspector pipe. All six native-host attempts remain unsupported transports. The readable WKWebView reference also lacks these transports, so the results do not establish inspection prevention.

The failed custom launch left a research browser running during the first pass. The runner now records existing instances before each target. Its final cleanup stops only newly launched instances of the exact executable and waits for exit. The repeated run exercised this cleanup for all three targets. A separate process check found no remaining research executable.

The result file records executable hashes and cleanup outcomes. Native input and capture protection were not tested. The console lock flag was true, native UI calls failed, and the rebuilt probe lacked effective grants. These conditions remain test blockers, not browser protection results. Safari Web Inspector still needs a separate matched attachment test.
