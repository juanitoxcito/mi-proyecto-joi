[app]

# (str) Title of your application
title = My Kivy App

# (str) Package name
package.name = org.yourpackage.myapp

# (str) Package domain (needed for android/ios packaging)
package.domain = org.yourpackage

source.dir = .

# (str) Application version
version = 0.1

# (list) Application requirements
requirements = python3,kivy

# (str) The category of the app.
# choose from: 'games', 'communication', 'education', 'social', 'travel', 'design'
#              'sports', 'lifestyle', 'health', 'finance', 'business', 'music',
#              'photo', 'tools', 'utilities'
# app_category = 'utilities'

# (list) Permissions
android.permissions = INTERNET

# (int) Android API target level (e.g. 27, 28, 29). Will default to 27 if not set.
# android.api = 27

# (int) Minimum API required to run the app (e.g. 19 or 21). Will default to 21 if not set.
# android.minapi = 21

# (int) Android SDK version to use
# android.sdk = 27

# (str) Android NDK version to use
# android.ndk = 21b

# (bool) If False, the app will not be debuggable.
android.debug = True

# (bool) If True, don't add the `__pycache__` folders and `.pyo` files
# android.no-build-copy-py = True

# (str) The directory where the apk will be stored
# bin_dir = bin

# (bool) If True, the previous app splash screen will be disabled
# android.disable_previous_app_splash = False
