[app]

# (str) Title of your application
title = Mi Proyecto Joi

# (str) Package name
package.name = miproyectojoi
# (str) Package domain (needed for android/ios packaging)
package.domain = org.test

# (str) Application version
version = 0.1

# (list) Requirements (usually python3, kivy and kivy-examples)
requirements = python3,kivy,cython,aidl

# (str) Kivy version to use
# The default is a stable release, to use a nightly, specify the commit hash or `master`
kivy.version = 2.3.0

# (str) Source code where the main.py lives
source.dir = .

# (list) List of exclusions
source.exclude_dirs = tests, bin

# (str) Logo for your application.
# icon.filename = %(source.dir)s/data/icon.png

# (list) List of desktop entries for your application.
# desktop = MyApp.desktop

# (list) List of files to install in the data folder
# install_data_dirs = data

# (str) Android entry point, default is 'org.kivy.android.PythonActivity'
# android.entrypoint = org.kivy.android.PythonActivity

# (str) Android SDK version to use
android.api = 29

# (str) Minimum Android SDK version to support
android.minapi = 26

# (str) Android NDK version to use
android.ndk = 25b

# (str) Android SDK location (if not set, buildozer will try to download it)
# android.sdk = 27

# (bool) Auto accept SDK license
android.accept_sdk_license = True

# (list) Android permissions
# android.permissions = INTERNET

# (bool) Debug mode. If False, disables debugging information and optimizes for size.
debug = True

# (bool) True if you want to log verbose output.
verbose = False

# (list) List of allowed orientations
# orientation = portrait

# (list) Exclude folders or files from distribution for specific platforms
# exclude_patterns = *.pyc, *.pyo, *.kvi

# (str) Set the Android application theme. It can be a theme defined in Android API,
# or a custom theme, if defined in the AndroidManifest.xml.
# android.theme = "@android:style/Theme.NoTitleBar"

# (str) The default value for the Android target SDK. If you set `android.api`, this will be `android.api`.
# android.target_sdk_version = 27

# (str) The default value for the Android build tools version.
# android.build_tools = 29.0.3

# (str) The default value for the Android SDK tools version.
# android.sdk_tools = 26.1.1
