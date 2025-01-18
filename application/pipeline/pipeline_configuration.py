from enum import Enum

from clapy import (AuthenticationVerifier, AuthorisationEnforcer,
                   EntityExistenceChecker, InputPortValidator,
                   InputTypeValidator, Interactor, PersistenceRuleValidator,
                   PipeConfiguration, PipeConfigurationOption,
                   RequiredInputValidator)


class PipelineConfiguration(Enum):

    DEFAULT = [
        PipeConfiguration(AuthenticationVerifier),
        PipeConfiguration(AuthorisationEnforcer),
        PipeConfiguration(RequiredInputValidator, PipeConfigurationOption.INSERT, should_ignore_failures = True),
        PipeConfiguration(InputTypeValidator, PipeConfigurationOption.INSERT, should_ignore_failures = True),
        PipeConfiguration(EntityExistenceChecker),
        PipeConfiguration(InputPortValidator),
        PipeConfiguration(PersistenceRuleValidator),
        PipeConfiguration(Interactor)
    ]
