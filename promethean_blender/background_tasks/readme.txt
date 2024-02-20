These background tasks are scripts designed to be passed to a new blender process via command line arguments. 
These functions are not called directly in the main plugin, a new blender process is created to handle them

In order to access modules from the rest of the plugin, we need to append the directory to sys.path