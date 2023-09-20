from enum import Enum

from clapy import InputTypeValidator, Interactor, PipeConfiguration, PipeConfigurationOption, RequiredInputValidator


class PipelineConfiguration(Enum):

    DefaultConfiguration = [
        PipeConfiguration(RequiredInputValidator, PipeConfigurationOption.INSERT, True),
        PipeConfiguration(InputTypeValidator, PipeConfigurationOption.INSERT, True),
        PipeConfiguration(Interactor)
    ]
