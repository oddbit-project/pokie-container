from rick.resource.config import EnvironmentConfig
from pokie.config.template import BaseConfigTemplate, PgConfigTemplate, TestConfigTemplate
from pokie.core import FlaskApplication
from pokie.core.factories.pgsql import PgSqlFactory


# base configuration
class Config(EnvironmentConfig, BaseConfigTemplate, PgConfigTemplate, TestConfigTemplate):
    TEST_MANAGE_DB = True
    TEST_DB_SSL = False


def build_pokie():
    # load configuration from ENV
    cfg = Config().build()

    # modules to load & initialize
    modules = ['pokie.contrib.auth', 'pokie_container']

    # factories to run
    factories = [PgSqlFactory]

    # build app
    pokie_app = FlaskApplication(cfg)
    flask_app = pokie_app.build(modules, factories)
    return pokie_app, flask_app


main, app = build_pokie()

# =============================================================================

if __name__ == '__main__':
    main.cli()
