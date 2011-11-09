#!/opt/local/bin/python
def main():
    from buscall.util import setup_for_testing
    setup_for_testing()

    from buscall import app
    from buscall import models, views, forms
    from google.appengine.ext import db
    from flaskext.script import Shell, Manager

    def _make_context():
        return {
            "app": app,
            "models": models,
            "views": views,
            "forms": forms,
            "db": db,
        }
    
    manager = Manager(app)
    manager.add_command("shell", Shell(make_context=_make_context))
    manager.run()

if __name__ == "__main__":
    import sys
    from main import get_updated_sys_path
    sys.path = get_updated_sys_path()
    main()
