from enum import Enum

from clapy import (AuthenticationVerifier, AuthorisationEnforcer,
                   EntityExistenceChecker, InputPortValidator,
                   InputTypeValidator, Interactor, PipeConfiguration,
                   PipeConfigurationOption, RequiredInputValidator)


class PipelineConfiguration(Enum):

    DefaultConfiguration = [
        PipeConfiguration(AuthenticationVerifier),
        PipeConfiguration(AuthorisationEnforcer),
        PipeConfiguration(RequiredInputValidator, PipeConfigurationOption.INSERT),
        PipeConfiguration(InputTypeValidator, PipeConfigurationOption.INSERT),
        PipeConfiguration(EntityExistenceChecker),
        PipeConfiguration(InputPortValidator),
        PipeConfiguration(Interactor)
    ]
