from clapy import IUseCaseInvoker

from application.pipeline.pipeline_configuration import PipelineConfiguration

DEFAULT_PIPELINE = PipelineConfiguration.DEFAULT.value

class BaseController:
    def __init__(self, use_case_invoker: IUseCaseInvoker):
        self._use_case_invoker = use_case_invoker
