from dependency_injector import containers, providers


class AdminContainer(containers.DeclarativeContainer):

    config = providers.Configuration()
