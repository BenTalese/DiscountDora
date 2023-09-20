from clapy import IUseCaseInvoker


class BaseController:
    def __init__(self, use_case_invoker: IUseCaseInvoker):
        self._use_case_invoker = use_case_invoker
